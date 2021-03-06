import csv

from datamart_materialize.utils import SimpleConverter


DATE_COLUMN_LABEL = 'date'
VALUE_COLUMN_LABEL = 'value'


def pivot_table(source_filename, dest_fileobj, except_columns):
    with open(source_filename, 'r') as src_fp:
        src = iter(csv.reader(src_fp))
        dst = csv.writer(dest_fileobj)

        # Read original columns, some are carried over
        try:
            orig_columns = next(src)
        except StopIteration:
            raise ValueError("Empty table")
        carried_columns = [orig_columns[i] for i in except_columns]

        # Generate new header
        dst.writerow(carried_columns + [DATE_COLUMN_LABEL, VALUE_COLUMN_LABEL])

        # Indexes of date columns
        date_indexes = [
            i for i in range(len(orig_columns))
            if i not in except_columns
        ]
        dates = [
            name for i, name in enumerate(orig_columns)
            if i not in except_columns
        ]

        for row in src:
            carried_values = [row[i] for i in except_columns]
            for date, date_idx in zip(dates, date_indexes):
                dst.writerow(carried_values + [date, row[date_idx]])


class PivotConverter(SimpleConverter):
    """Adapter converting a TSV file to CSV.
    """
    def __init__(self, writer, *, except_columns):
        super(PivotConverter, self).__init__(writer)
        self.except_columns = except_columns

    def transform(self, source_filename, dest_fileobj):
        pivot_table(source_filename, dest_fileobj, self.except_columns)
