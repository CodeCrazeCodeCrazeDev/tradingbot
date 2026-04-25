"""
Idea #32: IoT Sensor Networks
==============================
Real-time data from industrial IoT sensors.
"""

import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class SensorReading:
    sensor_id: str
    value: float
    timestamp: datetime
    sensor_type: str
    location: str


class IoTSensorNetwork:
    """Process IoT sensor data for trading signals."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.sensors: Dict[str, List[SensorReading]] = {}
        self.initialized = False
        self.metrics = {"readings_processed": 0, "anomalies_detected": 0}
        
    async def initialize(self):
        logger.info("Initializing IoT Sensor Network")
        self.initialized = True
        
    async def process_reading(self, sensor_id: str, value: float, 
                               sensor_type: str, location: str) -> Dict[str, Any]:
        if not self.initialized:
            await self.initialize()
        
        reading = SensorReading(sensor_id, value, datetime.now(), sensor_type, location)
        if sensor_id not in self.sensors:
            self.sensors[sensor_id] = []
        self.sensors[sensor_id].append(reading)
        if len(self.sensors[sensor_id]) > 1000:
            self.sensors[sensor_id] = self.sensors[sensor_id][-500:]
        
        self.metrics["readings_processed"] += 1
        
        anomaly = self._detect_anomaly(sensor_id, value)
        if anomaly:
            self.metrics["anomalies_detected"] += 1
        
        return {"sensor_id": sensor_id, "value": value, "anomaly": anomaly}
    
    def _detect_anomaly(self, sensor_id: str, value: float) -> bool:
        if sensor_id not in self.sensors or len(self.sensors[sensor_id]) < 10:
            return False
        values = [r.value for r in self.sensors[sensor_id][-100:]]
        mean, std = np.mean(values), np.std(values)
        return abs(value - mean) > 3 * std if std > 0 else False
    
    async def get_factory_activity(self, location: str) -> Dict[str, Any]:
        """Estimate factory activity from sensor data."""
        relevant = [r for readings in self.sensors.values() for r in readings if r.location == location]
        if not relevant:
            return {"location": location, "activity_level": 0.0}
        activity = np.mean([r.value for r in relevant[-100:]])
        return {"location": location, "activity_level": float(activity), "sensor_count": len(relevant)}
    
    async def get_energy_consumption(self) -> Dict[str, Any]:
        """Aggregate energy consumption data."""
        energy_sensors = {k: v for k, v in self.sensors.items() if "energy" in k.lower()}
        if not energy_sensors:
            return {"total_consumption": 0.0}
        total = sum(readings[-1].value for readings in energy_sensors.values() if readings)
        return {"total_consumption": float(total), "sensor_count": len(energy_sensors)}
    
    def get_metrics(self) -> Dict[str, Any]:
        return {**self.metrics, "active_sensors": len(self.sensors)}
    
    async def shutdown(self):
        self.sensors.clear()
        self.initialized = False
        logger.info("IoT Sensor Network shutdown complete")
