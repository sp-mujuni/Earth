import random
from datetime import datetime, timedelta

def generate_weather():
    return random.choice(['sunny/clear', 'windy', 'cloudy'])

def simulate_month(output_file):
    start_date = datetime(2025, 1, 7) 
    end_date = start_date + timedelta(days=30)  # Simulate for 30 days
    current_date = start_date
    rain_days = random.sample([0, 2, 4], 3)  # Choose 3 Mondays, Wednesdays, or Fridays

    with open(output_file, 'w') as f:
        while current_date < end_date:
            for hour in range(24):
                for minute in range(0, 60, 15):  # 15-minute intervals
                    current_time = current_date.replace(hour=hour, minute=minute)
                    
                    if current_date.weekday() < 5 and current_date.day in rain_days and hour == 14 and minute < 45:
                        weather = 'rainy'
                    else:
                        weather = generate_weather()
                    
                    f.write(f"{current_time.strftime('%Y-%m-%d %I:%M %p')} - {weather}\n")
            
            current_date += timedelta(days=1)

if __name__ == "__main__":
    output_file = "weather_simulation.txt"
    simulate_month(output_file)
    print(f"Weather simulation completed. Results saved to {output_file}")