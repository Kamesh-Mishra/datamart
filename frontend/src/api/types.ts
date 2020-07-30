export interface AugmentationTask {
  data: SearchResult;
}

export interface ColumnAggregations {
  [columnName: string]: string[];
}

// Keep in sync with datamart_profiler's temporal_aggregation_keys
export enum TemporalResolution {
  YEAR = 'year',
  MONTH = 'month',
  WEEK = 'week',
  DAY = 'day',
  HOUR = 'hour',
  MINUTE = 'minute',
  SECOND = 'second',
}

export interface AugmentationInfo {
  type: string;
  left_columns: number[][];
  left_columns_names: string[][];
  right_columns: number[][];
  right_columns_names: string[][];
  agg_functions?: ColumnAggregations;
}

export interface SpatialCoverage {
  lat?: string;
  lon?: string;
  address?: string;
  point?: string;
  admin?: string;
  ranges: Array<{
    range: {
      coordinates: [[number, number], [number, number]];
      type: 'envelope';
    };
  }>;
}

export interface Metadata {
  id: string;
  filename?: string;
  name: string;
  description: string;
  size: number;
  nb_rows: number;
  columns: ColumnMetadata[];
  date: string;
  materialize: {};
  nb_profiled_rows: number;
  sample: string;
  source: string;
  version: string;
  spatial_coverage?: SpatialCoverage[];
}

export interface ColumnMetadata {
  name: string;
  structural_type: string;
  semantic_types: string[];
  num_distinct_values?: number;
  coverage?: Array<{}>;
  mean?: number;
  stddev?: number;
  plot?: PlotVega;
}

export interface PlotVega {
  type: string;
  data:
    | NumericalDataVegaFormat[]
    | TemporalDataVegaFormat[]
    | CategoricalDataVegaFormat[];
}

export interface SearchResult {
  id: string;
  score: number;
  // join_columns: Array<[string, string]>;
  metadata: Metadata;
  augmentation?: AugmentationInfo;
  supplied_id: string | null;
  supplied_resource_id: string | null;
  d3m_dataset_description: {};
  sample: string[][];
}

export interface SearchResponse {
  results: SearchResult[];
}

export interface Variable {
  type: string;
}

export interface TemporalVariable {
  type: 'temporal_variable';
  start?: string;
  end?: string;
  granularity?: string;
}

export interface GeoSpatialVariable {
  type: 'geospatial_variable';
  latitude1: string;
  longitude1: string;
  latitude2: string;
  longitude2: string;
}

export type FilterVariables = TemporalVariable | GeoSpatialVariable;

export interface QuerySpec {
  keywords?: string;
  source?: string[];
  variables: FilterVariables[];
}

interface RelatedToFileBase {
  kind: string;
  name: string;
  fileSize: number;
}

export interface RelatedToLocalFile extends RelatedToFileBase {
  kind: 'localFile';
  token: string;
}

export interface RelatedToSearchResult extends RelatedToFileBase {
  kind: 'searchResult';
  datasetId: string;
}

export type RelatedFile = RelatedToLocalFile | RelatedToSearchResult;

export interface NumericalDataVegaFormat {
  count: number;
  bin_start: number;
  bin_end: number;
}

export interface TemporalDataVegaFormat {
  count: number;
  date_start: string;
  date_end: string;
}

export interface CategoricalDataVegaFormat {
  count: number;
  bin: string;
}

export enum InfoBoxType {
  DETAIL = 'DETAIL',
  AUGMENTATION = 'AUGMENTATION',
}

export enum Annotation {
  ADD = 'ADD',
  REMOVE = 'REMOVE',
}

export enum TypesCategory {
  STRUCTURAL = 'STRUCTURAL',
  SEMANTIC = 'SEMANTIC',
}

export interface Session {
  session_id: string;
  format?: string;
  format_options?: { [key: string]: string | number };
  system_name: string;
}
