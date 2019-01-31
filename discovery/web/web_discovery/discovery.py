import aiohttp
import asyncio
from bs4 import BeautifulSoup
import logging
import os
import uuid
from yarl import URL

from datamart_core import AsyncDiscoverer
from datamart_core.common import log_future, msg2json


logger = logging.getLogger(__name__)


def get_mimetype(resp):
    if 'Content-Type' not in resp.headers:
        return None
    else:
        mimetype = resp.headers['Content-Type']
        mimetype = mimetype.split(';', 1)[0]
        return mimetype.lower()


class DatasetFinder(object):
    GOOD_TYPES = {'text/csv', 'application/octet-stream', 'text/plain'}
    BAD_EXTS = ['.html', '.html5', '.php', '.php5']
    MAX_FILES = 20

    def __init__(self):
        super(DatasetFinder, self).__init__()

        self.loop = asyncio.get_event_loop()

    async def find_datasets(self, session, obj):
        logger.info("Processing URL %s", obj['url'])
        async with session.get(obj['url'], headers=obj.get('headers')) as resp:
            mimetype = get_mimetype(resp)
            if mimetype in self.GOOD_TYPES:
                logger.info("Checking file...")
                url = await self.check_file(resp)
                if url:
                    yield url
                    return
            elif mimetype != 'text/html':
                logger.info("Ignoring URL, type is %s", mimetype)
                return
            content = await resp.read()

        # Find all links
        logger.info("Processing HTML...")
        soup = BeautifulSoup(content, 'html5lib')
        links = soup.find_all('a')
        links = list({elem.attrs['href'] for elem in links
                      if 'href' in elem.attrs})
        links = list(str(resp.url.join(URL(link))) for link in links)
        total_links = len(links)

        # If some of the links are CSVs
        csvs = [link for link in links if link.endswith('.csv')]
        if csvs:
            # Only keep those
            links = csvs
        else:
            # Else, at least discard the obviously HTML ones
            newlinks = []
            for link in links:
                link = link.lower()
                if not any(link.endswith(ext) for ext in self.BAD_EXTS):
                    newlinks.append(link)
            links = newlinks

        logger.info("Got %d/%d links...", len(links), total_links)
        if len(links) > 20:
            logger.info("Too many links, only checking %d", self.MAX_FILES)
            links = links[:self.MAX_FILES]

        # Try the links
        async def do_link(link):
            async with session.get(link) as resp:
                mimetype = get_mimetype(resp)
                if mimetype and mimetype not in self.GOOD_TYPES:
                    logger.info("Ignoring %s", mimetype)
                return await self.check_file(resp)

        futures = []
        for link in links:
            futures.append(self.loop.create_task(
                do_link(link)
            ))
        for url in asyncio.as_completed(futures):
            try:
                url = await url
            except Exception:
                logger.exception("Exception processing link")
            else:
                if url:
                    yield url
        logger.info("URL processing done")

    async def check_file(self, resp):
        content = await resp.content.read(8192)
        lines = content.splitlines()
        if len(lines) <= 5:
            logging.info("File: got only %d lines?", len(lines))
            return
        if not lines[1].strip():
            del lines[1]
        commas = [line.count(b',') for line in lines[1:-1]]
        if not commas[1]:
            logging.info("File: no commas")
            return
        if any(c != commas[1] for c in commas):
            logging.info("File: inconsistent number of commas")
            return
        logging.info("File: is a CSV")
        return str(resp.url)


class WebDiscoverer(AsyncDiscoverer, DatasetFinder):
    """Base class for web discoverer, which can find CSV in web pages.
    """
    async def _process_url(self, session, obj, metadata=None):
        async for url in self.find_datasets(session, obj):
            if metadata is None:
                metadata = {}

            dataset_id = 'datamart.url.%s' % (
                uuid.uuid5(uuid.NAMESPACE_URL, str(url)).hex
            )

            await self.record_dataset(dict(direct_url=url),
                                      metadata,
                                      dataset_id=dataset_id)


class UrlDiscoverer(WebDiscoverer):
    """Discoverer reading URLs of interest from an AMQP queue.
    """

    async def _run(self):
        await super(WebDiscoverer, self)._run()

        # Declare the urls queue
        self.urls_queue = await self.channel.declare_queue('urls')

        log_future(self.loop.create_task(self._consume_urls()),
                   logger,
                   should_never_exit=True)

    async def _consume_urls(self):
        async with aiohttp.ClientSession() as session:
            async for message in self.urls_queue:
                obj = msg2json(message)
                log_future(
                    self.loop.create_task(self._process_url(session, obj)),
                    logger,
                    message="Exception processing URL",
                )
                message.ack()


BING_API_KEY = os.environ['BING_API_KEY']


async def bing_search(session, keywords):
    logger.info("Bing search: %s", keywords)
    async with session.get(
        'https://api.cognitive.microsoft.com/bing/v7.0/search',
        params={'q': keywords},
        headers={'Ocp-Apim-Subscription-Key': BING_API_KEY},
    ) as resp:
        data = await resp.json()

    results = data['webPages']['value']
    logger.info("Got %d/%d results", len(results),
                data['webPages']['totalEstimatedMatches'])
    return results


class BingDiscoverer(WebDiscoverer):
    """Discoverer feeding on-demand queries into Bing Web Search.
    """
    async def handle_query(self, query, publish):
        keywords = set()
        if 'about' in query.get('dataset', {}):
            keywords.update(query['dataset']['about'].split())
        # TODO: Keywords from other interesting fields?
        keywords = ' '.join(keywords)

        async with aiohttp.ClientSession() as session:
            results = await bing_search(session, keywords)

            # Try all the top results
            futures = []
            for page in results:
                futures.append(self.loop.create_task(
                    self._process_url(session, dict(url=page['url']))
                ))
            await asyncio.wait(futures)
