from .models import RideOffer
from network.models import Edge
from network.utils import shortest_path
from trips.models import Trip


def get_remaining_route(trip):
    route   = trip.route or []
    visited = trip.visited_nodes or []

    if not visited or not route:
        return route

    last_visited = visited[-1]

    try:
        idx = route.index(last_visited)

        # if trip hasn't started yet
        # include current node in remaining
        if trip.status == 'SCHEDULED':
            return route[idx:]      

        # if trip is active
        # driver already left current node
        return route[idx + 1:]      

    except ValueError:
        return route


def is_request_matching_trip(trip, pickup_node_id, drop_node_id):

    #available seats checking
    if trip.available_seats <= 0:
        return False

    #trip not finished cheking
    if trip.current_node_id == trip.end_node_id:
        return False

    # remaining route checking 
    remaining_route = get_remaining_route(trip)

    if not remaining_route:
        return False

    # both pickup AND drop must be exactly on remaining route
    if pickup_node_id not in remaining_route:
        return False        

    if drop_node_id not in remaining_route:
        return False       

    # pickup must come BEFORE drop in route
    pickup_index = remaining_route.index(pickup_node_id)
    drop_index   = remaining_route.index(drop_node_id)

    if pickup_index >= drop_index:
        return False        

    return True            

def find_matching_trips(pickup_node_id, drop_node_id):
    matches = []

    active_trips = Trip.objects.filter(
        status__in=['SCHEDULED', 'ACTIVE'],   
        available_seats__gt=0
    )

    for trip in active_trips:
        if is_request_matching_trip(trip, pickup_node_id, drop_node_id):
            matches.append({
                'trip_id':         trip.id,
                'driver':          trip.driver.username,
                'status':          trip.status,
                'remaining_route': get_remaining_route(trip)
            })
    return matches

def calculate_all_fares(trip, new_route, all_requests):
    UNIT_PRICE = 10.0
    BASE_FEE   = 5.0

    # for each hop, count how many passengers are in the car
    fares = {req.id: 0.0 for req in all_requests}

    for i in range(len(new_route) - 1):
        current = new_route[i]
        next_n  = new_route[i + 1]

        # count passengers in car at this hop
        passengers_in_car = []
        for req in all_requests:
            pickup = req.pickup_node.id
            drop   = req.drop_node.id

            # passenger is in car if current hop is between their pickup and drop
            if pickup in new_route and drop in new_route:
                pickup_idx = new_route.index(pickup)
                drop_idx   = new_route.index(drop)
                hop_idx    = new_route.index(current)

                if pickup_idx <= hop_idx < drop_idx:
                    passengers_in_car.append(req.id)

        n = len(passengers_in_car)
        if n > 0:
            hop_cost = UNIT_PRICE * (1 / n)
            for req_id in passengers_in_car:
                if req_id in fares:
                    fares[req_id] += hop_cost

    # add base fee to each passenger
    for req_id in fares:
        fares[req_id] += BASE_FEE

    return fares


def calculate_detour_and_fare(trip, ride_request):
    remaining_route  = get_remaining_route(trip)

    if not remaining_route:
        return 0, 0

    current_node_id  = remaining_route[0]
    pickup_node_id   = ride_request.pickup_node.id
    drop_node_id     = ride_request.drop_node.id
    end_node_id      = remaining_route[-1]

    # 1. original remaining distance
    original_remaining_dist = 0
    for i in range(len(remaining_route) - 1):
        u    = remaining_route[i]
        v    = remaining_route[i + 1]
        edge = Edge.objects.filter(from_node_id=u, to_node_id=v).first()  # ← directed only
        original_remaining_dist += (edge.distance if edge else 1.0)

    # 2. new distance after picking up passenger
    dist_to_pickup,  path_to_pickup  = shortest_path(current_node_id, pickup_node_id)
    dist_passenger,  path_passenger  = shortest_path(pickup_node_id,  drop_node_id)
    dist_to_end,     path_to_end     = shortest_path(drop_node_id,    end_node_id)

    if not path_to_pickup or not path_passenger or not path_to_end:  # ← fixed check
        return float('inf'), 0

    new_remaining_dist = dist_to_pickup + dist_passenger + dist_to_end

    #detour = difference
    detour    = max(0, new_remaining_dist - original_remaining_dist)

    #construct new full route
    new_route = path_to_pickup[:-1] + path_passenger[:-1] + path_to_end

    #get all confirmed passengers + new requesting passenger
    accepted_offers     = RideOffer.objects.filter(trip=trip, status='accepted')
    confirmed_requests  = [offer.ride_request for offer in accepted_offers]
    all_requests        = confirmed_requests + [ride_request]

    #calculate fare
    all_fares      = calculate_all_fares(trip, new_route, all_requests)
    passenger_fare = all_fares.get(ride_request.id, 0.0)

    return round(detour, 2), round(passenger_fare, 2)

