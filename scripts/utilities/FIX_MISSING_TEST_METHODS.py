"""
Fix Missing Methods in Test Integration Modules
Adds stub methods required by test_critical_integration.py
"""

import os

# DataQuarantine - add validate_data method
data_quarantine_addition = '''
    
    def validate_data(self, data):
        """
        Validate data for quality issues
        
        Args:
            data: DataFrame or dict to validate
            
        Returns:
            tuple: (is_clean, issues) where issues is list of problems found
        """
        issues = []
        
        # Check for None/NaN values
        if hasattr(data, 'isnull'):
            if data.isnull().any().any():
                issues.append("Contains NaN values")
        
        # Check for negative prices
        if hasattr(data, 'get'):
            if 'price' in data and (data['price'] < 0).any():
                issues.append("Contains negative prices")
        
        is_clean = len(issues) == 0
        return is_clean, issues
'''

# SignalProvenance - add create_provenance method
signal_provenance_addition = '''
    
    def create_provenance(self, signal_id: str, metadata: dict):
        """
        Create provenance record for a signal
        
        Args:
            signal_id: Unique signal identifier
            metadata: Dictionary with signal metadata
            
        Returns:
            Provenance record dictionary
        """
        provenance = {
            'signal_id': signal_id,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata,
            'quality_score': metadata.get('confidence', 0.5)
        }
        
        # Store in history
        if signal_id not in self.provenance_history:
            self.provenance_history[signal_id] = []
        self.provenance_history[signal_id].append(provenance)
        
        return provenance
'''

# NewsGating - add should_gate_trading method
news_gating_addition = '''
    
    def should_gate_trading(self, news_event: dict) -> tuple[bool, str]:
        """
        Determine if trading should be gated based on news event
        
        Args:
            news_event: Dictionary with news event details
            
        Returns:
            tuple: (should_gate, reason)
        """
        impact = news_event.get('impact', 'LOW')
        
        if impact == 'HIGH':
            return True, f"High-impact news: {news_event.get('event', 'Unknown')}"
        elif impact == 'MEDIUM':
            return False, "Medium-impact news - proceed with caution"
        else:
            return False, "Low-impact news"
'''

# MarketImpactModel - add calculate_impact method  
market_impact_addition = '''
    
    def calculate_impact(self, order_size: float, market_data: dict) -> float:
        """
        Calculate market impact of an order
        
        Args:
            order_size: Size of the order
            market_data: Market data dictionary
            
        Returns:
            Estimated market impact in basis points
        """
        # Simple linear impact model
        avg_volume = market_data.get('avg_volume', 1000000)
        participation_rate = order_size / avg_volume
        
        # Impact increases with square root of participation rate
        impact_bps = 10 * (participation_rate ** 0.5) * 10000
        
        return min(impact_bps, 100)  # Cap at 100 bps
'''

def add_method_to_file(filepath, method_code, class_name):
    """Add method to a class in a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the class definition
        class_pattern = f'class {class_name}'
        if class_pattern not in content:
            print(f"  ❌ Class {class_name} not found in {filepath}")
            return False
        
        # Check if method already exists
        if 'def validate_data' in content or 'def create_provenance' in content or \
           'def should_gate_trading' in content or 'def calculate_impact' in content:
            print(f"  ✓ Methods already exist in {filepath}")
            return True
        
        # Add method before the last line (usually empty or __main__)
        lines = content.split('\n')
        
        # Find a good insertion point (before __main__ or at end of class)
        insert_idx = len(lines) - 1
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip().startswith('if __name__'):
                insert_idx = i - 1
                break
            elif lines[i].strip() and not lines[i].startswith(' ') and i > 0:
                # Found end of class
                insert_idx = i
                break
        
        # Insert the method
        lines.insert(insert_idx, method_code)
        
        # Write back
        with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(lines))
        
        print(f"  ✅ Added method to {filepath}")
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    print("=" * 80)
    print("FIXING MISSING TEST METHODS")
    print("=" * 80)
    print()
    
    fixes = [
        ('trading_bot/database/data_quarantine.py', data_quarantine_addition, 'DataQuarantine'),
        ('trading_bot/signals/signal_provenance.py', signal_provenance_addition, 'SignalProvenance'),
        ('trading_bot/signals/news_gating.py', news_gating_addition, 'NewsGating'),
        ('trading_bot/execution/market_impact.py', market_impact_addition, 'MarketImpactModel'),
    ]
    
    success_count = 0
    for filepath, method_code, class_name in fixes:
        print(f"Processing {filepath}...")
        if add_method_to_file(filepath, method_code, class_name):
            success_count += 1
    
    print()
    print("=" * 80)
    print(f"COMPLETE: {success_count}/{len(fixes)} files updated")
    print("=" * 80)

if __name__ == "__main__":
    main()
