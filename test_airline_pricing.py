"""
Test script for airline-style pricing engine
"""
from datetime import datetime, timedelta
from app.engine.airline_pricing import AirlineStylePricingEngine, AIEnhancedPricingEngine

def test_basic_pricing():
    """Test basic pricing calculations"""
    print("\n" + "="*60)
    print("TEST 1: Basic Pricing Engine")
    print("="*60)
    
    engine = AirlineStylePricingEngine(base_rate=8000, total_rooms=22)
    
    # Test case 1: Early booking, low occupancy
    check_in = datetime.now() + timedelta(days=45)
    pricing = engine.calculate_price(check_in, current_occupancy_pct=10.0)
    
    print(f"\nScenario: 45 days ahead, 10% occupancy")
    print(f"Base Rate: ETB {pricing['base_rate']:,.2f}")
    print(f"Optimized Rate: ETB {pricing['optimized_rate']:,.2f}")
    print(f"Discount: {pricing['discount_applied_pct']}%")
    print(f"Savings: ETB {pricing['savings_etb']:,.2f}")
    print(f"Fare Class: {pricing['fare_class']}")
    print(f"Time Bucket: {pricing['pricing_factors']['time_bucket']}")
    print(f"Inventory Bucket: {pricing['pricing_factors']['inventory_bucket']}")
    
    # Test case 2: Last minute, high occupancy
    check_in = datetime.now() + timedelta(days=3)
    pricing = engine.calculate_price(check_in, current_occupancy_pct=85.0)
    
    print(f"\nScenario: 3 days ahead, 85% occupancy")
    print(f"Base Rate: ETB {pricing['base_rate']:,.2f}")
    print(f"Optimized Rate: ETB {pricing['optimized_rate']:,.2f}")
    print(f"Discount: {pricing['discount_applied_pct']}%")
    print(f"Fare Class: {pricing['fare_class']}")
    
    # Test case 3: Weekend premium
    check_in = datetime.now() + timedelta(days=20)
    # Make it a Friday
    while check_in.weekday() != 4:
        check_in += timedelta(days=1)
    
    pricing = engine.calculate_price(check_in, current_occupancy_pct=25.0, is_weekend=True)
    
    print(f"\nScenario: Weekend booking, 25% occupancy")
    print(f"Base Rate: ETB {pricing['base_rate']:,.2f}")
    print(f"Optimized Rate: ETB {pricing['optimized_rate']:,.2f}")
    print(f"Discount: {pricing['discount_applied_pct']}%")
    print(f"Weekend Premium: {pricing['pricing_factors']['weekend_premium']}x")


def test_fare_classes():
    """Test fare class generation"""
    print("\n" + "="*60)
    print("TEST 2: Fare Classes (Like Airline Booking)")
    print("="*60)
    
    engine = AIEnhancedPricingEngine(base_rate=8000, total_rooms=22)
    check_in = datetime.now() + timedelta(days=30)
    
    fare_classes = engine.get_available_fare_classes(
        check_in,
        current_occupancy_pct=15.0,
        rooms_remaining=20
    )
    
    print(f"\nAvailable Fare Classes for {check_in.strftime('%Y-%m-%d')}:")
    print(f"Current Occupancy: 15% | Rooms Remaining: 20\n")
    
    for fc in fare_classes:
        print(f"{fc['class']:10} | ETB {fc['rate']:>8,.2f} | {fc['discount_pct']:>5.1f}% OFF | {fc['available_rooms']:>2} rooms")
        print(f"           | {fc['description']}")
        print(f"           | Refundable: {fc['restrictions']['refundable']}, Changeable: {fc['restrictions']['changeable']}")
        print()


def test_ai_demand_prediction():
    """Test AI demand prediction"""
    print("\n" + "="*60)
    print("TEST 3: AI Demand Prediction")
    print("="*60)
    
    engine = AIEnhancedPricingEngine(base_rate=8000, total_rooms=22)
    
    # Test different dates
    test_dates = [
        datetime(2026, 9, 11),   # Meskel (Ethiopian New Year)
        datetime(2026, 1, 19),   # Timkat
        datetime(2026, 7, 15),   # Summer
        datetime(2026, 4, 20),   # Rainy season
        datetime(2026, 5, 9),    # Weekend (Saturday)
        datetime(2026, 5, 12),   # Weekday (Tuesday)
    ]
    
    print("\nDemand Predictions:")
    print(f"{'Date':<12} | {'Day':<10} | {'Demand':<8} | {'Level':<12} | {'Strategy'}")
    print("-" * 80)
    
    for date in test_dates:
        demand = engine.predict_demand(date)
        level = "Very High" if demand >= 1.3 else "High" if demand >= 1.1 else "Normal" if demand >= 0.9 else "Low" if demand >= 0.7 else "Very Low"
        strategy = "Increase prices" if demand >= 1.3 else "Premium pricing" if demand >= 1.1 else "Standard" if demand >= 0.9 else "Moderate discount" if demand >= 0.7 else "Aggressive discount"
        
        print(f"{date.strftime('%Y-%m-%d'):<12} | {date.strftime('%A'):<10} | {demand:>6.2f}x | {level:<12} | {strategy}")


def test_pricing_table():
    """Display the complete pricing table"""
    print("\n" + "="*60)
    print("TEST 4: Complete Pricing Table")
    print("="*60)
    
    table = AirlineStylePricingEngine.PRICING_TABLE
    
    print("\nTime Until Arrival vs. Inventory Occupancy")
    print("-" * 80)
    print(f"{'Time Bucket':<15} | {'Inventory':<10} | {'Discount':<10} | {'Inventory Extent'}")
    print("-" * 80)
    
    for (time_bucket, inv_bucket), (discount, extent) in sorted(table.items()):
        time_desc = {
            ">30": ">1 month",
            "30-14": "1mo-2wks",
            "14-7": "2wks-1wk",
            "<7": "<1 week"
        }[time_bucket]
        
        print(f"{time_desc:<15} | {inv_bucket:<10} | {discount:>6.1f}% | {extent:>6.1f}%")


if __name__ == "__main__":
    print("\n🚀 AIRLINE-STYLE PRICING ENGINE TEST SUITE")
    print("Testing Kuraz AI Revenue Management System")
    
    test_basic_pricing()
    test_fare_classes()
    test_ai_demand_prediction()
    test_pricing_table()
    
    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETED")
    print("="*60)
    print("\nNext Steps:")
    print("1. Start backend: python -m uvicorn app.main:app --reload")
    print("2. Test API: curl -X POST http://localhost:8000/api/pricing/calculate ...")
    print("3. Integrate with booking flow")
    print("4. Add ML models for Phase 4")
    print()
