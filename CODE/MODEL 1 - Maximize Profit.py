from docplex.mp.model import Model

# Initialize the CPLEX model
mdl = Model("ABSA_Oil")

# Example data structures (Fill these with your actual data)
costs = {
    "processing": 19,
    "crude": {"Azeri BTC": 57, "Poseidon Streams": 48, "Laguna": 35, "Snøhvit Condensate": 71},
    }

prices = {
    "Gasoline-87": 90.45,
    "Gasoline-89": 93.66,
    "Gasoline-92": 95.50,
    "Jet fuel": 61.25,
    "Diesel fuel": 101.64,
    "Heating oil": 66.36
    }

capacities = {
    "UK": 735000,
    "Spain": 625000,
    "Poland": 540000,
    "Greece": 400000,
    }

monthly_supply_quotas = {
    "Azeri BTC": 645000,        # The monthly supply quota for Azeri BTC
    "Poseidon Streams": 575000, # The monthly supply quota for Poseidon Streams
    "Laguna": 550000,           # The monthly supply quota for Laguna
    "Snøhvit Condensate": 645000 # The monthly supply quota for Snøhvit Condensate
    }

demands = {
    "Gasoline-87": {"Greece": 35000, "Poland": 22000, "Spain": 76000, "UK": 98000},
    "Gasoline-89": {"Greece": 45000, "Poland": 38000, "Spain": 103000, "UK": 52000},
    "Gasoline-92": {"Greece": 50000, "Poland": 60000, "Spain": 83000, "UK": 223000},
    "Jet fuel": {"Greece": 20000, "Poland": 25000, "Spain": 47000, "UK": 127000},
    "Diesel fuel": {"Greece": 75000, "Poland": 35000, "Spain": 125000, "UK": 87000},
    "Heating oil": {"Greece": 25000, "Poland": 205000, "Spain": 30000, "UK": 13000}
    }

# Decision Variables
purchase_vars = mdl.continuous_var_dict(costs["crude"].keys(), name="purchase")
production_vars = mdl.continuous_var_matrix(prices.keys(), capacities.keys(), name="produce")
def discounted_revenue(production, demand, price):
    # Calculate excess production
    excess = mdl.max(production - demand, 0)
    # Calculate revenue for production up to demand
    regular_revenue = mdl.min(production, demand) * price
    # Calculate revenue for excess production at a discounted rate
    excess_revenue = excess * price * 0.93
    return regular_revenue + excess_revenue

# Objective Function: Maximize Profit
revenue = mdl.sum(discounted_revenue(production_vars[prod, ref], demands[prod].get(ref, 0), prices[prod])
                  for prod in prices for ref in capacities)
crude_cost = mdl.sum(costs["crude"][crude] * purchase_vars[crude] for crude in costs["crude"])
production_cost = mdl.sum(costs["processing"] * production_vars[prod, ref] for prod in prices for ref in capacities)
mdl.maximize(revenue - crude_cost - production_cost)

# Constraints
# 1. Production meets or exceeds demand in each region for each product
for prod, regions in demands.items():
    for region, demand in regions.items():
        mdl.add_constraint(production_vars[prod, region] >= demand)

# 2. Refinery capacities are not exceeded
for ref, capacity in capacities.items():
    mdl.add_constraint(mdl.sum(production_vars[prod, ref] for prod in prices) <= capacity)

# 3. Crude oil purchases and usage with a 1:1 ratio
for crude in costs["crude"]:
    total_crude_usage = mdl.sum(production_vars[prod, ref] for prod in prices for ref in capacities) / len(costs["crude"])
    mdl.add_constraint(purchase_vars[crude] == total_crude_usage)

# 4. Respecting the monthly supply quota for each crude type
for crude, quota in monthly_supply_quotas.items():
    mdl.add_constraint(purchase_vars[crude] <= quota)

# Solve the model
solution = mdl.solve()

# Print the solution
if solution:
    print("The objective value (Profit) is: ", mdl.objective_value)

    # Calculate and print Revenue
    revenue_value = sum(prices[prod] * production_vars[prod, ref].solution_value for prod in prices for ref in capacities)
    print("Total Revenue: ", revenue_value)

    # Calculate and print Crude Cost
    crude_cost_value = sum(costs["crude"][crude] * purchase_vars[crude].solution_value for crude in costs["crude"])
    print("Total Crude Cost: ", crude_cost_value)

    # Calculate and print Production Cost
    production_cost_value = sum(costs["processing"] * production_vars[prod, ref].solution_value for prod in prices for ref in capacities)
    print("Total Production Cost: ", production_cost_value)

    # Print decision variable values
    for crude in costs["crude"]:
        print(f"Purchased {purchase_vars[crude].solution_value} barrels of {crude} crude oil.")
    for prod in prices:
        for ref in capacities:
            print(f"Produced {production_vars[prod, ref].solution_value} barrels of {prod} in {ref} refinery.")
    # Print the total barrels produced in each refinery
    # Print the total barrels produced in each refinery and the amount of crude transported from each port
    for ref in capacities:
        total_barrels_in_refinery = sum(production_vars[prod, ref].solution_value for prod in prices)
        #print(f"Total barrels produced in {ref} refinery: {total_barrels_in_refinery}")

        # Calculate and print the amount of crude oil transported from each port to this refinery
        crude_oil_per_port = total_barrels_in_refinery / 4
        print(f"Crude oil transported from each port to {ref} refinery: {crude_oil_per_port}")

else:
    print("No solution found")