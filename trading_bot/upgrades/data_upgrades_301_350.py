"""
Data Infrastructure Upgrades 301-350
"""
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple, Generator
from datetime import datetime, timedelta
from enum import Enum, auto
from collections import deque
import hashlib
import json

# UPGRADE 301: Data Pipeline Manager
class DataPipelineManager:
    def __init__(self):
        self.stages: List[callable] = []
        self.cache: Dict[str, Any] = {}
        
    def add_stage(self, stage: callable):
        self.stages.append(stage)
        
    def process(self, data: Any) -> Any:
        result = data
        for stage in self.stages:
            result = stage(result)
        return result
    
    def process_batch(self, batch: List[Any]) -> List[Any]:
        return [self.process(item) for item in batch]

# UPGRADE 302: Data Validator
class DataValidator:
    def __init__(self):
        self.rules: List[callable] = []
        
    def add_rule(self, rule: callable):
        self.rules.append(rule)
        
    def validate(self, data: Dict) -> Tuple[bool, List[str]]:
        errors = []
        for rule in self.rules:
            try:
                if not rule(data): errors.append(rule.__name__)
            except Exception as e: errors.append(f"{rule.__name__}: {e}")
        return len(errors) == 0, errors

# UPGRADE 303: Data Cleaner
class DataCleaner:
    def clean_ohlcv(self, data: List[Dict]) -> List[Dict]:
        cleaned = []
        for d in data:
            if all(k in d for k in ['open', 'high', 'low', 'close', 'volume']):
                if d['high'] >= d['low'] and d['high'] >= max(d['open'], d['close']):
                    if d['low'] <= min(d['open'], d['close']) and d['volume'] >= 0:
                        cleaned.append(d)
        return cleaned
    
    def fill_missing(self, data: List[Dict], method: str = 'forward') -> List[Dict]:
        if not data: return data
        result = [data[0].copy()]
        for i in range(1, len(data)):
            row = data[i].copy()
            for key in row:
                if row[key] is None:
                    if method == 'forward': row[key] = result[-1].get(key)
                    elif method == 'zero': row[key] = 0
            result.append(row)
        return result

# UPGRADE 304: Data Normalizer
class DataNormalizer:
    def __init__(self):
        self.stats: Dict[str, Dict] = {}
        
    def fit(self, data: List[Dict]):
        if not data: return
        for key in data[0]:
            values = [d[key] for d in data if isinstance(d.get(key), (int, float))]
            if values:
                self.stats[key] = {'min': min(values), 'max': max(values), 'mean': np.mean(values), 'std': np.std(values) or 1}
                
    def normalize(self, data: Dict, method: str = 'minmax') -> Dict:
        result = {}
        for key, value in data.items():
            if key in self.stats and isinstance(value, (int, float)):
                s = self.stats[key]
                if method == 'minmax':
                    result[key] = (value - s['min']) / (s['max'] - s['min'] + 0.0001)
                elif method == 'zscore':
                    result[key] = (value - s['mean']) / s['std']
            else:
                result[key] = value
        return result

# UPGRADE 305: Data Aggregator
class DataAggregator:
    def aggregate_ohlcv(self, data: List[Dict], period: int) -> List[Dict]:
        if not data or period <= 1: return data
        result = []
        for i in range(0, len(data), period):
            chunk = data[i:i+period]
            if chunk:
                result.append({
                    'open': chunk[0]['open'],
                    'high': max(c['high'] for c in chunk),
                    'low': min(c['low'] for c in chunk),
                    'close': chunk[-1]['close'],
                    'volume': sum(c['volume'] for c in chunk),
                    'timestamp': chunk[0].get('timestamp')
                })
        return result

# UPGRADE 306: Data Resampler
class DataResampler:
    def resample(self, data: List[Dict], from_tf: str, to_tf: str) -> List[Dict]:
        tf_minutes = {'1m': 1, '5m': 5, '15m': 15, '1h': 60, '4h': 240, '1d': 1440}
        from_mins = tf_minutes.get(from_tf, 1)
        to_mins = tf_minutes.get(to_tf, 1)
        if to_mins <= from_mins: return data
        ratio = to_mins // from_mins
        aggregator = DataAggregator()
        return aggregator.aggregate_ohlcv(data, ratio)

# UPGRADE 307: Time Series Aligner
class TimeSeriesAligner:
    def align(self, series1: List[Dict], series2: List[Dict], key: str = 'timestamp') -> Tuple[List[Dict], List[Dict]]:
        times1 = {d[key]: d for d in series1}
        times2 = {d[key]: d for d in series2}
        common = sorted(set(times1.keys()) & set(times2.keys()))
        return [times1[t] for t in common], [times2[t] for t in common]

# UPGRADE 308: Data Merger
class DataMerger:
    def merge(self, datasets: List[List[Dict]], key: str = 'timestamp') -> List[Dict]:
        merged = {}
        for dataset in datasets:
            for item in dataset:
                k = item.get(key)
                if k not in merged: merged[k] = {}
                merged[k].update(item)
        return [v for k, v in sorted(merged.items())]

# UPGRADE 309: Data Splitter
class DataSplitter:
    def train_test_split(self, data: List, train_ratio: float = 0.8) -> Tuple[List, List]:
        split_idx = int(len(data) * train_ratio)
        return data[:split_idx], data[split_idx:]
    
    def train_val_test_split(self, data: List, train: float = 0.7, val: float = 0.15) -> Tuple[List, List, List]:
        train_idx = int(len(data) * train)
        val_idx = int(len(data) * (train + val))
        return data[:train_idx], data[train_idx:val_idx], data[val_idx:]

# UPGRADE 310: Sliding Window Generator
class SlidingWindowGenerator:
    def generate(self, data: List, window_size: int, step: int = 1) -> Generator:
        for i in range(0, len(data) - window_size + 1, step):
            yield data[i:i + window_size]
    
    def generate_xy(self, data: List, lookback: int, horizon: int = 1) -> Tuple[List, List]:
        X, y = [], []
        for i in range(lookback, len(data) - horizon + 1):
            X.append(data[i-lookback:i])
            y.append(data[i:i+horizon])
        return X, y

# UPGRADE 311: Data Buffer
class DataBuffer:
    def __init__(self, max_size: int = 10000):
        self.buffer: deque = deque(maxlen=max_size)
        
    def add(self, item: Any):
        self.buffer.append(item)
        
    def get_recent(self, n: int) -> List:
        return list(self.buffer)[-n:]
    
    def get_all(self) -> List:
        return list(self.buffer)
    
    def clear(self):
        self.buffer.clear()

# UPGRADE 312: Ring Buffer
class RingBuffer:
    def __init__(self, size: int):
        self.size = size
        self.buffer = [None] * size
        self.index = 0
        self.count = 0
        
    def append(self, item: Any):
        self.buffer[self.index] = item
        self.index = (self.index + 1) % self.size
        self.count = min(self.count + 1, self.size)
        
    def get(self, idx: int) -> Any:
        if idx >= self.count: return None
        actual_idx = (self.index - self.count + idx) % self.size
        return self.buffer[actual_idx]
    
    def to_list(self) -> List:
        return [self.get(i) for i in range(self.count)]

# UPGRADE 313: Priority Queue
class PriorityQueue:
    def __init__(self):
        self.heap: List[Tuple[float, Any]] = []
        
    def push(self, priority: float, item: Any):
        self.heap.append((priority, item))
        self._sift_up(len(self.heap) - 1)
        
    def pop(self) -> Any:
        if not self.heap: return None
        self._swap(0, len(self.heap) - 1)
        item = self.heap.pop()
        if self.heap: self._sift_down(0)
        return item[1]
    
    def _sift_up(self, idx: int):
        while idx > 0:
            parent = (idx - 1) // 2
            if self.heap[idx][0] < self.heap[parent][0]:
                self._swap(idx, parent)
                idx = parent
            else: break
                
    def _sift_down(self, idx: int):
        while True:
            smallest = idx
            left, right = 2 * idx + 1, 2 * idx + 2
            if left < len(self.heap) and self.heap[left][0] < self.heap[smallest][0]: smallest = left
            if right < len(self.heap) and self.heap[right][0] < self.heap[smallest][0]: smallest = right
            if smallest != idx:
                self._swap(idx, smallest)
                idx = smallest
            else: break
                
    def _swap(self, i: int, j: int):
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]

# UPGRADE 314: LRU Cache
class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache: Dict[str, Any] = {}
        self.order: List[str] = []
        
    def get(self, key: str) -> Any:
        if key not in self.cache: return None
        self.order.remove(key)
        self.order.append(key)
        return self.cache[key]
    
    def put(self, key: str, value: Any):
        if key in self.cache:
            self.order.remove(key)
        elif len(self.cache) >= self.capacity:
            oldest = self.order.pop(0)
            del self.cache[oldest]
        self.cache[key] = value
        self.order.append(key)

# UPGRADE 315: Time-Based Cache
class TimeBasedCache:
    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self.cache: Dict[str, Dict] = {}
        
    def get(self, key: str) -> Any:
        if key not in self.cache: return None
        entry = self.cache[key]
        if (datetime.utcnow() - entry['time']).total_seconds() > self.ttl:
            del self.cache[key]
            return None
        return entry['value']
    
    def put(self, key: str, value: Any):
        self.cache[key] = {'value': value, 'time': datetime.utcnow()}
    
    def cleanup(self):
        now = datetime.utcnow()
        expired = [k for k, v in self.cache.items() if (now - v['time']).total_seconds() > self.ttl]
        for k in expired: del self.cache[k]

# UPGRADE 316: Data Compressor
class DataCompressor:
    def compress_ohlcv(self, data: List[Dict]) -> bytes:
        compressed = []
        for d in data:
            compressed.append(f"{d['open']},{d['high']},{d['low']},{d['close']},{d['volume']}")
        return '\n'.join(compressed).encode()
    
    def decompress_ohlcv(self, data: bytes) -> List[Dict]:
        lines = data.decode().split('\n')
        result = []
        for line in lines:
            if line:
                parts = line.split(',')
                result.append({
                    'open': float(parts[0]), 'high': float(parts[1]),
                    'low': float(parts[2]), 'close': float(parts[3]), 'volume': float(parts[4])
                })
        return result

# UPGRADE 317: Data Serializer
class DataSerializer:
    def serialize(self, data: Any) -> str:
        return json.dumps(data, default=str)
    
    def deserialize(self, data: str) -> Any:
        return json.loads(data)
    
    def serialize_numpy(self, arr: np.ndarray) -> Dict:
        return {'data': arr.tolist(), 'dtype': str(arr.dtype), 'shape': arr.shape}
    
    def deserialize_numpy(self, data: Dict) -> np.ndarray:
        return np.array(data['data'], dtype=data['dtype']).reshape(data['shape'])

# UPGRADE 318: Data Checksum Calculator
class DataChecksumCalculator:
    def calculate(self, data: Any) -> str:
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()
    
    def verify(self, data: Any, checksum: str) -> bool:
        return self.calculate(data) == checksum

# UPGRADE 319: Data Version Manager
class DataVersionManager:
    def __init__(self):
        self.versions: Dict[str, List[Dict]] = {}
        
    def save_version(self, name: str, data: Any, metadata: Dict = None):
        if name not in self.versions: self.versions[name] = []
        version = len(self.versions[name]) + 1
        self.versions[name].append({
            'version': version, 'data': data, 'metadata': metadata or {},
            'timestamp': datetime.utcnow().isoformat()
        })
        
    def get_version(self, name: str, version: int = None) -> Any:
        if name not in self.versions: return None
        if version is None: return self.versions[name][-1]['data']
        for v in self.versions[name]:
            if v['version'] == version: return v['data']
        return None

# UPGRADE 320: Data Diff Calculator
class DataDiffCalculator:
    def diff(self, old: Dict, new: Dict) -> Dict:
        added = {k: v for k, v in new.items() if k not in old}
        removed = {k: v for k, v in old.items() if k not in new}
        changed = {k: {'old': old[k], 'new': new[k]} for k in old if k in new and old[k] != new[k]}
        return {'added': added, 'removed': removed, 'changed': changed}
    
    def apply_diff(self, data: Dict, diff: Dict) -> Dict:
        result = data.copy()
        for k in diff.get('removed', {}): result.pop(k, None)
        result.update(diff.get('added', {}))
        for k, v in diff.get('changed', {}).items(): result[k] = v['new']
        return result

# UPGRADE 321: Data Snapshot Manager
class DataSnapshotManager:
    def __init__(self):
        self.snapshots: List[Dict] = []
        
    def create_snapshot(self, data: Dict, label: str = None) -> int:
        snapshot_id = len(self.snapshots)
        self.snapshots.append({
            'id': snapshot_id, 'data': data.copy(), 'label': label,
            'timestamp': datetime.utcnow().isoformat()
        })
        return snapshot_id
    
    def restore_snapshot(self, snapshot_id: int) -> Dict:
        if 0 <= snapshot_id < len(self.snapshots):
            return self.snapshots[snapshot_id]['data'].copy()
        return {}

# UPGRADE 322: Data Stream Processor
class DataStreamProcessor:
    def __init__(self):
        self.handlers: List[callable] = []
        self.buffer: deque = deque(maxlen=1000)
        
    def add_handler(self, handler: callable):
        self.handlers.append(handler)
        
    def process(self, item: Any):
        self.buffer.append(item)
        for handler in self.handlers:
            try: handler(item)
            except Exception as e: pass
            
    def get_buffer(self) -> List:
        return list(self.buffer)

# UPGRADE 323: Event Sourcing Store
class EventSourcingStore:
    def __init__(self):
        self.events: List[Dict] = []
        
    def append_event(self, event_type: str, data: Dict):
        self.events.append({
            'id': len(self.events), 'type': event_type, 'data': data,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    def replay(self, handler: callable, from_id: int = 0):
        for event in self.events[from_id:]:
            handler(event)
            
    def get_events(self, event_type: str = None) -> List[Dict]:
        if event_type is None: return self.events
        return [e for e in self.events if e['type'] == event_type]

# UPGRADE 324: CQRS Command Handler
class CQRSCommandHandler:
    def __init__(self):
        self.handlers: Dict[str, callable] = {}
        
    def register(self, command_type: str, handler: callable):
        self.handlers[command_type] = handler
        
    def execute(self, command_type: str, data: Dict) -> Any:
        if command_type not in self.handlers:
            raise ValueError(f"Unknown command: {command_type}")
        return self.handlers[command_type](data)

# UPGRADE 325: CQRS Query Handler
class CQRSQueryHandler:
    def __init__(self):
        self.handlers: Dict[str, callable] = {}
        
    def register(self, query_type: str, handler: callable):
        self.handlers[query_type] = handler
        
    def query(self, query_type: str, params: Dict) -> Any:
        if query_type not in self.handlers:
            raise ValueError(f"Unknown query: {query_type}")
        return self.handlers[query_type](params)

# UPGRADE 326: Data Partitioner
class DataPartitioner:
    def partition_by_time(self, data: List[Dict], key: str, interval: str) -> Dict[str, List[Dict]]:
        partitions = {}
        for item in data:
            ts = item.get(key)
            if ts:
                if interval == 'day': partition_key = ts[:10]
                elif interval == 'hour': partition_key = ts[:13]
                else: partition_key = ts[:7]
                if partition_key not in partitions: partitions[partition_key] = []
                partitions[partition_key].append(item)
        return partitions
    
    def partition_by_value(self, data: List[Dict], key: str, n_partitions: int) -> Dict[int, List[Dict]]:
        partitions = {i: [] for i in range(n_partitions)}
        for item in data:
            value = item.get(key, 0)
            partition_id = hash(str(value)) % n_partitions
            partitions[partition_id].append(item)
        return partitions

# UPGRADE 327: Data Sharding Manager
class DataShardingManager:
    def __init__(self, n_shards: int = 4):
        self.n_shards = n_shards
        self.shards: Dict[int, List] = {i: [] for i in range(n_shards)}
        
    def get_shard(self, key: str) -> int:
        return hash(key) % self.n_shards
    
    def add(self, key: str, data: Any):
        shard_id = self.get_shard(key)
        self.shards[shard_id].append({'key': key, 'data': data})
        
    def get(self, key: str) -> Any:
        shard_id = self.get_shard(key)
        for item in self.shards[shard_id]:
            if item['key'] == key: return item['data']
        return None

# UPGRADE 328: Data Replication Manager
class DataReplicationManager:
    def __init__(self, n_replicas: int = 3):
        self.n_replicas = n_replicas
        self.replicas: List[Dict] = [{} for _ in range(n_replicas)]
        
    def write(self, key: str, value: Any) -> int:
        success_count = 0
        for replica in self.replicas:
            replica[key] = value
            success_count += 1
        return success_count
    
    def read(self, key: str) -> Any:
        for replica in self.replicas:
            if key in replica: return replica[key]
        return None
    
    def read_quorum(self, key: str) -> Any:
        values = [r.get(key) for r in self.replicas if key in r]
        if len(values) >= self.n_replicas // 2 + 1:
            return max(set(values), key=values.count)
        return None

# UPGRADE 329: Write-Ahead Log
class WriteAheadLog:
    def __init__(self):
        self.log: List[Dict] = []
        self.committed: int = 0
        
    def append(self, operation: str, data: Dict) -> int:
        lsn = len(self.log)
        self.log.append({'lsn': lsn, 'operation': operation, 'data': data, 'committed': False})
        return lsn
    
    def commit(self, lsn: int):
        if 0 <= lsn < len(self.log):
            self.log[lsn]['committed'] = True
            self.committed = max(self.committed, lsn + 1)
            
    def recover(self) -> List[Dict]:
        return [entry for entry in self.log if entry['committed']]

# UPGRADE 330: Data Consistency Checker
class DataConsistencyChecker:
    def check_ohlcv(self, data: List[Dict]) -> List[str]:
        issues = []
        for i, d in enumerate(data):
            if d['high'] < d['low']: issues.append(f"Row {i}: high < low")
            if d['high'] < max(d['open'], d['close']): issues.append(f"Row {i}: high < open/close")
            if d['low'] > min(d['open'], d['close']): issues.append(f"Row {i}: low > open/close")
            if d['volume'] < 0: issues.append(f"Row {i}: negative volume")
        return issues
    
    def check_monotonic(self, data: List[Dict], key: str) -> bool:
        values = [d[key] for d in data if key in d]
        return all(values[i] <= values[i+1] for i in range(len(values)-1))

# UPGRADE 331: Data Quality Scorer
class DataQualityScorer:
    def score(self, data: List[Dict]) -> Dict[str, float]:
        if not data: return {'completeness': 0, 'validity': 0, 'consistency': 0}
        total_fields = len(data[0]) * len(data)
        missing = sum(1 for d in data for v in d.values() if v is None)
        completeness = 1 - missing / total_fields
        checker = DataConsistencyChecker()
        issues = checker.check_ohlcv(data) if 'open' in data[0] else []
        validity = 1 - len(issues) / len(data) if data else 1
        return {'completeness': completeness, 'validity': validity, 'overall': (completeness + validity) / 2}

# UPGRADE 332: Data Lineage Tracker
class DataLineageTracker:
    def __init__(self):
        self.lineage: Dict[str, Dict] = {}
        
    def register_source(self, data_id: str, source: str, metadata: Dict = None):
        self.lineage[data_id] = {'source': source, 'metadata': metadata or {}, 'transformations': [], 'created': datetime.utcnow().isoformat()}
        
    def add_transformation(self, data_id: str, transformation: str, params: Dict = None):
        if data_id in self.lineage:
            self.lineage[data_id]['transformations'].append({
                'transformation': transformation, 'params': params or {},
                'timestamp': datetime.utcnow().isoformat()
            })
            
    def get_lineage(self, data_id: str) -> Dict:
        return self.lineage.get(data_id, {})

# UPGRADE 333: Data Catalog
class DataCatalog:
    def __init__(self):
        self.catalog: Dict[str, Dict] = {}
        
    def register(self, name: str, schema: Dict, description: str = '', tags: List[str] = None):
        self.catalog[name] = {
            'schema': schema, 'description': description, 'tags': tags or [],
            'created': datetime.utcnow().isoformat(), 'updated': datetime.utcnow().isoformat()
        }
        
    def search(self, query: str) -> List[str]:
        results = []
        for name, info in self.catalog.items():
            if query.lower() in name.lower() or query.lower() in info['description'].lower():
                results.append(name)
            elif any(query.lower() in tag.lower() for tag in info['tags']):
                results.append(name)
        return results
    
    def get_schema(self, name: str) -> Dict:
        return self.catalog.get(name, {}).get('schema', {})

# UPGRADE 334: Schema Registry
class SchemaRegistry:
    def __init__(self):
        self.schemas: Dict[str, List[Dict]] = {}
        
    def register(self, name: str, schema: Dict) -> int:
        if name not in self.schemas: self.schemas[name] = []
        version = len(self.schemas[name]) + 1
        self.schemas[name].append({'version': version, 'schema': schema, 'timestamp': datetime.utcnow().isoformat()})
        return version
    
    def get_schema(self, name: str, version: int = None) -> Dict:
        if name not in self.schemas: return {}
        if version is None: return self.schemas[name][-1]['schema']
        for s in self.schemas[name]:
            if s['version'] == version: return s['schema']
        return {}
    
    def is_compatible(self, name: str, new_schema: Dict) -> bool:
        current = self.get_schema(name)
        if not current: return True
        return set(current.keys()).issubset(set(new_schema.keys()))

# UPGRADE 335: Data Profiler
class DataProfiler:
    def profile(self, data: List[Dict]) -> Dict[str, Dict]:
        if not data: return {}
        profile = {}
        for key in data[0]:
            values = [d[key] for d in data if d.get(key) is not None]
            if not values: continue
            if all(isinstance(v, (int, float)) for v in values):
                profile[key] = {
                    'type': 'numeric', 'count': len(values), 'min': min(values), 'max': max(values),
                    'mean': np.mean(values), 'std': np.std(values), 'nulls': len(data) - len(values)
                }
            else:
                profile[key] = {
                    'type': 'categorical', 'count': len(values), 'unique': len(set(values)),
                    'top': max(set(values), key=values.count), 'nulls': len(data) - len(values)
                }
        return profile

# UPGRADE 336: Data Sampler
class DataSampler:
    def random_sample(self, data: List, n: int) -> List:
        if n >= len(data): return data
        indices = np.random.choice(len(data), n, replace=False)
        return [data[i] for i in indices]
    
    def stratified_sample(self, data: List[Dict], key: str, n: int) -> List[Dict]:
        groups = {}
        for item in data:
            k = item.get(key)
            if k not in groups: groups[k] = []
            groups[k].append(item)
        n_per_group = max(1, n // len(groups))
        result = []
        for group in groups.values():
            result.extend(self.random_sample(group, min(n_per_group, len(group))))
        return result
    
    def reservoir_sample(self, stream: Generator, k: int) -> List:
        reservoir = []
        for i, item in enumerate(stream):
            if i < k: reservoir.append(item)
            else:
                j = np.random.randint(0, i + 1)
                if j < k: reservoir[j] = item
        return reservoir

# UPGRADE 337: Data Deduplicator
class DataDeduplicator:
    def deduplicate(self, data: List[Dict], keys: List[str] = None) -> List[Dict]:
        seen = set()
        result = []
        for item in data:
            if keys:
                key = tuple(item.get(k) for k in keys)
            else:
                key = tuple(sorted(item.items()))
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result
    
    def find_duplicates(self, data: List[Dict], keys: List[str]) -> List[List[int]]:
        groups = {}
        for i, item in enumerate(data):
            key = tuple(item.get(k) for k in keys)
            if key not in groups: groups[key] = []
            groups[key].append(i)
        return [indices for indices in groups.values() if len(indices) > 1]

# UPGRADE 338: Data Imputer
class DataImputer:
    def impute_mean(self, data: List[Dict], columns: List[str]) -> List[Dict]:
        means = {}
        for col in columns:
            values = [d[col] for d in data if d.get(col) is not None and isinstance(d[col], (int, float))]
            means[col] = np.mean(values) if values else 0
        result = []
        for item in data:
            new_item = item.copy()
            for col in columns:
                if new_item.get(col) is None: new_item[col] = means[col]
            result.append(new_item)
        return result
    
    def impute_median(self, data: List[Dict], columns: List[str]) -> List[Dict]:
        medians = {}
        for col in columns:
            values = [d[col] for d in data if d.get(col) is not None and isinstance(d[col], (int, float))]
            medians[col] = np.median(values) if values else 0
        result = []
        for item in data:
            new_item = item.copy()
            for col in columns:
                if new_item.get(col) is None: new_item[col] = medians[col]
            result.append(new_item)
        return result

# UPGRADE 339: Outlier Detector
class OutlierDetector:
    def detect_iqr(self, data: List[float], multiplier: float = 1.5) -> List[int]:
        q1, q3 = np.percentile(data, [25, 75])
        iqr = q3 - q1
        lower, upper = q1 - multiplier * iqr, q3 + multiplier * iqr
        return [i for i, v in enumerate(data) if v < lower or v > upper]
    
    def detect_zscore(self, data: List[float], threshold: float = 3.0) -> List[int]:
        mean, std = np.mean(data), np.std(data) or 1
        return [i for i, v in enumerate(data) if abs((v - mean) / std) > threshold]

# UPGRADE 340: Data Encoder
class DataEncoder:
    def __init__(self):
        self.mappings: Dict[str, Dict] = {}
        
    def fit_label_encoder(self, column: str, values: List):
        unique = sorted(set(values))
        self.mappings[column] = {v: i for i, v in enumerate(unique)}
        
    def transform_label(self, column: str, value: Any) -> int:
        return self.mappings.get(column, {}).get(value, -1)
    
    def one_hot_encode(self, column: str, value: Any, n_categories: int) -> List[int]:
        idx = self.transform_label(column, value)
        encoding = [0] * n_categories
        if 0 <= idx < n_categories: encoding[idx] = 1
        return encoding

# UPGRADE 341: Data Binning
class DataBinning:
    def equal_width(self, data: List[float], n_bins: int) -> List[int]:
        min_val, max_val = min(data), max(data)
        bin_width = (max_val - min_val) / n_bins
        return [min(n_bins - 1, int((v - min_val) / bin_width)) for v in data]
    
    def equal_frequency(self, data: List[float], n_bins: int) -> List[int]:
        sorted_indices = np.argsort(data)
        bin_size = len(data) // n_bins
        bins = [0] * len(data)
        for i, idx in enumerate(sorted_indices):
            bins[idx] = min(n_bins - 1, i // bin_size)
        return bins
    
    def custom_bins(self, data: List[float], edges: List[float]) -> List[int]:
        return [sum(1 for e in edges if v >= e) for v in data]

# UPGRADE 342: Feature Scaler
class FeatureScaler:
    def __init__(self):
        self.params: Dict[str, Dict] = {}
        
    def fit_minmax(self, name: str, data: List[float]):
        self.params[name] = {'type': 'minmax', 'min': min(data), 'max': max(data)}
        
    def fit_standard(self, name: str, data: List[float]):
        self.params[name] = {'type': 'standard', 'mean': np.mean(data), 'std': np.std(data) or 1}
        
    def transform(self, name: str, value: float) -> float:
        if name not in self.params: return value
        p = self.params[name]
        if p['type'] == 'minmax':
            return (value - p['min']) / (p['max'] - p['min'] + 0.0001)
        return (value - p['mean']) / p['std']

# UPGRADE 343: Time Series Differencer
class TimeSeriesDifferencer:
    def difference(self, data: List[float], order: int = 1) -> List[float]:
        result = data
        for _ in range(order):
            result = [result[i] - result[i-1] for i in range(1, len(result))]
        return result
    
    def inverse_difference(self, diff_data: List[float], first_values: List[float]) -> List[float]:
        result = list(first_values)
        for d in diff_data:
            result.append(result[-1] + d)
        return result

# UPGRADE 344: Lag Creator
class LagCreator:
    def create_lags(self, data: List[float], lags: List[int]) -> Dict[str, List[float]]:
        result = {}
        for lag in lags:
            result[f'lag_{lag}'] = [None] * lag + data[:-lag] if lag > 0 else data
        return result
    
    def create_rolling(self, data: List[float], window: int, func: str = 'mean') -> List[float]:
        result = [None] * (window - 1)
        for i in range(window - 1, len(data)):
            window_data = data[i - window + 1:i + 1]
            if func == 'mean': result.append(np.mean(window_data))
            elif func == 'std': result.append(np.std(window_data))
            elif func == 'min': result.append(min(window_data))
            elif func == 'max': result.append(max(window_data))
        return result

# UPGRADE 345: Data Interpolator
class DataInterpolator:
    def linear(self, data: List[float]) -> List[float]:
        result = data.copy()
        for i in range(len(result)):
            if result[i] is None:
                prev_idx = next((j for j in range(i-1, -1, -1) if result[j] is not None), None)
                next_idx = next((j for j in range(i+1, len(result)) if result[j] is not None), None)
                if prev_idx is not None and next_idx is not None:
                    ratio = (i - prev_idx) / (next_idx - prev_idx)
                    result[i] = result[prev_idx] + ratio * (result[next_idx] - result[prev_idx])
                elif prev_idx is not None: result[i] = result[prev_idx]
                elif next_idx is not None: result[i] = result[next_idx]
        return result
    
    def spline(self, x: List[float], y: List[float], new_x: List[float]) -> List[float]:
        return [np.interp(nx, x, y) for nx in new_x]

# UPGRADE 346: Data Smoother
class DataSmoother:
    def moving_average(self, data: List[float], window: int) -> List[float]:
        result = []
        for i in range(len(data)):
            start = max(0, i - window + 1)
            result.append(np.mean(data[start:i+1]))
        return result
    
    def exponential(self, data: List[float], alpha: float = 0.3) -> List[float]:
        result = [data[0]]
        for i in range(1, len(data)):
            result.append(alpha * data[i] + (1 - alpha) * result[-1])
        return result
    
    def savitzky_golay(self, data: List[float], window: int = 5, order: int = 2) -> List[float]:
        if window % 2 == 0: window += 1
        half = window // 2
        result = data.copy()
        for i in range(half, len(data) - half):
            window_data = data[i - half:i + half + 1]
            result[i] = np.mean(window_data)
        return result

# UPGRADE 347: Data Transformer
class DataTransformer:
    def log_transform(self, data: List[float]) -> List[float]:
        return [np.log(max(0.0001, v)) for v in data]
    
    def sqrt_transform(self, data: List[float]) -> List[float]:
        return [np.sqrt(max(0, v)) for v in data]
    
    def box_cox(self, data: List[float], lmbda: float = 0.5) -> List[float]:
        if lmbda == 0: return self.log_transform(data)
        return [(max(0.0001, v) ** lmbda - 1) / lmbda for v in data]
    
    def inverse_box_cox(self, data: List[float], lmbda: float = 0.5) -> List[float]:
        if lmbda == 0: return [np.exp(v) for v in data]
        return [(v * lmbda + 1) ** (1 / lmbda) for v in data]

# UPGRADE 348: Data Augmenter
class DataAugmenter:
    def add_noise(self, data: List[float], std: float = 0.01) -> List[float]:
        return [v + np.random.normal(0, std) for v in data]
    
    def time_warp(self, data: List[float], sigma: float = 0.2) -> List[float]:
        n = len(data)
        warp = np.cumsum(np.random.normal(1, sigma, n))
        warp = warp / warp[-1] * (n - 1)
        return [np.interp(i, warp, data) for i in range(n)]
    
    def magnitude_warp(self, data: List[float], sigma: float = 0.2) -> List[float]:
        n = len(data)
        warp = np.random.normal(1, sigma, n)
        return [v * w for v, w in zip(data, warp)]

# UPGRADE 349: Data Generator
class DataGenerator:
    def generate_random_walk(self, n: int, start: float = 100, volatility: float = 0.02) -> List[float]:
        prices = [start]
        for _ in range(n - 1):
            change = np.random.normal(0, volatility)
            prices.append(prices[-1] * (1 + change))
        return prices
    
    def generate_ohlcv(self, n: int, start: float = 100) -> List[Dict]:
        data = []
        price = start
        for _ in range(n):
            open_p = price
            high = open_p * (1 + abs(np.random.normal(0, 0.01)))
            low = open_p * (1 - abs(np.random.normal(0, 0.01)))
            close = np.random.uniform(low, high)
            volume = np.random.randint(1000, 10000)
            data.append({'open': open_p, 'high': high, 'low': low, 'close': close, 'volume': volume})
            price = close
        return data

# UPGRADE 350: Data Export Manager
class DataExportManager:
    def to_csv(self, data: List[Dict], filepath: str = None) -> str:
        if not data: return ''
        headers = list(data[0].keys())
        lines = [','.join(headers)]
        for row in data:
            lines.append(','.join(str(row.get(h, '')) for h in headers))
        csv_content = '\n'.join(lines)
        return csv_content
    
    def to_json(self, data: Any) -> str:
        return json.dumps(data, default=str, indent=2)
    
    def from_csv(self, csv_content: str) -> List[Dict]:
        lines = csv_content.strip().split('\n')
        if not lines: return []
        headers = lines[0].split(',')
        result = []
        for line in lines[1:]:
            values = line.split(',')
            result.append({h: v for h, v in zip(headers, values)})
        return result
