

import simpy
import pandas as pd
import matplotlib.pyplot as plt

# Load dataset
bus_data = pd.read_csv('bus_trips_654.csv')

# Preprocess dataset
bus_data['start_time_dt'] = pd.to_datetime(bus_data['date'] + ' ' + bus_data['start_time'])
bus_data.sort_values('start_time_dt', inplace=True)
terminals = bus_data['start_terminal'].unique().tolist()

# Parameters
BUS_CAPACITY = 60
waiting_times = []
bus_utilization = {}

# SimPy environment
env = simpy.Environment()
bus_stops = {terminal: simpy.Store(env) for terminal in terminals}

# Passenger process
def passenger_process(env, arrival_min, start_terminal):
    yield env.timeout(arrival_min)
    passenger = {'arrival_time': env.now}
    yield bus_stops[start_terminal].put(passenger)

# Bus process
def bus_process(env, bus_id, route_data):
    total_passengers = 0
    for _, trip in route_data.iterrows():
        start = trip['start_terminal']
        end = trip['end_terminal']
        travel_time = trip['duration_in_mins']
        queue = bus_stops[start]
        boarded = 0
        while len(queue.items) > 0 and boarded < BUS_CAPACITY:
            passenger = yield queue.get()
            wait_time = env.now - passenger['arrival_time']
            waiting_times.append(wait_time)
            boarded += 1
            total_passengers += 1
        yield env.timeout(travel_time)
    bus_utilization[bus_id] = total_passengers

# Schedule passengers
start_sim = bus_data['start_time_dt'].min()
bus_data['arrival_min'] = (bus_data['start_time_dt'] - start_sim).dt.total_seconds() / 60

for idx, row in bus_data.iterrows():
    env.process(passenger_process(env, row['arrival_min'], row['start_terminal']))

# Schedule buses
for bus_id, bus_trips in bus_data.groupby('deviceid'):
    env.process(bus_process(env, bus_id, bus_trips))

# Run simulation
sim_duration = (bus_data['arrival_min'].max() + bus_data['duration_in_mins'].max()) * 1.2
env.run(until=sim_duration)

# Metrics
avg_waiting_time = sum(waiting_times)/len(waiting_times) if waiting_times else 0
total_passengers = sum(bus_utilization.values())
avg_bus_utilization = sum(bus_utilization.values())/len(bus_utilization)

# 3. Print summary statistics
print("\n=== Summary Statistics ===")
print(f"Average Waiting Time: {avg_waiting_time:.2f} minutes")
print(f"Total Passengers Served: {total_passengers}")
print(f"Average Bus Utilization: {avg_bus_utilization:.2f} passengers per bus")
print(f"Bus Utilization Range: {min(bus_utilization.values())} - {max(bus_utilization.values())}")

# Visualization
plt.hist(waiting_times, bins=50)
plt.xlabel("Passenger Waiting Time (minutes)")
plt.ylabel("Number of Passengers")
plt.title("Passenger Waiting Time Distribution")
plt.show()


# 2. Bus Utilization Bar Chart
plt.figure(figsize=(10,5))
plt.bar(bus_utilization.keys(), bus_utilization.values(), color='lightgreen', edgecolor='black')
plt.title("Bus Utilization per Bus (Passengers Served)")
plt.xlabel("Bus ID (deviceid)")
plt.ylabel("Passengers Carried")
plt.xticks(rotation=90)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()