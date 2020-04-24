import * as React from 'react';
import * as Icon from 'react-feather';
import { API_URL } from '../../config';
import { formatSize } from '../../utils';
import { SearchResult } from '../../api/types';
import { Description, DataTypes, DatasetColumns } from './Metadata';
import { AugmentationOptions } from './AugmentationOptions';
import { SearchQuery } from '../../api/rest';

interface SearchHitProps {
  searchQuery: SearchQuery;
  hit: SearchResult;
  onSearchHitExpand: (hit: SearchResult) => void;
  onSearchRelated: (datasetId: string) => void;
}

interface SearchHitState {
  hidden: boolean;
}

function DownloadViewDetails(props: {
  id: string;
  onSearchHitExpand: () => void;
  onSearchRelated: () => void;
}) {
  return (
    <div className="mt-2">
      <a
        className="btn btn-sm btn-outline-primary"
        href={`${API_URL}/download/${props.id}`}
      >
        <Icon.Download className="feather" /> Download
      </a>
      <button
        className="btn btn-sm btn-outline-primary ml-2"
        onClick={props.onSearchHitExpand}
      >
        <Icon.Info className="feather" /> View Details
      </button>
      <button
        className="btn btn-sm btn-outline-primary ml-2"
        onClick={props.onSearchRelated}
      >
        <Icon.Search className="feather" /> Search related
      </button>
    </div>
  );
}

function HitTitle(props: { hit: SearchResult }) {
  return (
    <span
      className="text-primary"
      style={{ fontSize: '1.2rem', fontFamily: 'Source Sans Pro' }}
    >
      {props.hit.metadata.name}{' '}
      <span className="small text-muted">
        ({formatSize(props.hit.metadata.size)})
      </span>
    </span>
  );
}

class SearchHit extends React.PureComponent<SearchHitProps, SearchHitState> {
  constructor(props: SearchHitProps) {
    super(props);
    this.state = {
      hidden: true,
    };
    this.onSearchHitExpand = this.onSearchHitExpand.bind(this);
    this.onSearchRelated = this.onSearchRelated.bind(this);
  }

  onSearchHitExpand() {
    this.props.onSearchHitExpand(this.props.hit);
  }

  onSearchRelated() {
    this.props.onSearchRelated(this.props.hit.id);
  }

  render() {
    const { hit, searchQuery } = this.props;
    return (
      <div className="card mb-4 shadow-sm d-flex flex-row">
        <div className="card-body d-flex flex-column">
          <HitTitle hit={hit} />
          <span className="small">{hit.metadata.source}</span>
          <Description hit={hit} label={false} />
          <DatasetColumns columns={hit.metadata.columns} label={false} />
          <DataTypes hit={hit} label={false} />
          <DownloadViewDetails
            id={hit.id}
            onSearchHitExpand={this.onSearchHitExpand}
            onSearchRelated={this.onSearchRelated}
          />
          <AugmentationOptions hit={hit} searchQuery={searchQuery} />
        </div>
        <div
          className="d-flex align-items-stretch"
          style={{ cursor: 'pointer' }}
          onClick={this.onSearchHitExpand}
        >
          <div style={{ margin: 'auto 2px' }}>
            <Icon.ChevronRight className="feather feather-lg" />
          </div>
        </div>
      </div>
    );
  }
}

export { SearchHit };
