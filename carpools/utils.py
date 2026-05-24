from .models import RideOffer, RideRequest
from network.models import Edge
from network.utils import shortest_path
from trips.models import Trip


def get_remaining_route(trip):
    route = trip.route or []
    current = trip.current_node_id

    if current not in route:
        return route

    idx = route.index(current)
    return route[idx:]  # from current node to end


def is_request_matching_trip(trip, pickup_node_id, drop_node_id):
    
    # 1. check available seats
    if trip.available_seats <= 0:
        return False

    # 2. check trip not already completed
    if trip.current_node_id == trip.end_node_id:
        return False

    remaining_route = get_remaining_route(trip)

    if not remaining_route:
        return False

    # 3. get all nodes within 2 hops of remaining route
    nearby_nodes = set()
    for node_id in remaining_route:
        nearby_nodes.add(node_id)

        edges_1 = Edge.objects.filter(from_node_id=node_id).values_list('to_node_id', flat=True)
        for n1 in edges_1:
            nearby_nodes.add(n1)

            edges_2 = Edge.objects.filter(from_node_id=n1).values_list('to_node_id', flat=True)
            for n2 in edges_2:
                nearby_nodes.add(n2)

    # 4. both pickup and drop must be within 2 nodes of route
    return pickup_node_id in nearby_nodes and drop_node_id in nearby_nodes


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

    # 3. detour = difference
    detour    = max(0, new_remaining_dist - original_remaining_dist)

    # 4. construct new full route
    new_route = path_to_pickup[:-1] + path_passenger[:-1] + path_to_end

    # 5. get all confirmed passengers + new requesting passenger
    accepted_offers     = RideOffer.objects.filter(trip=trip, status='accepted')
    confirmed_requests  = [offer.ride_request for offer in accepted_offers]
    all_requests        = confirmed_requests + [ride_request]

    # 6. calculate fare
    all_fares      = calculate_all_fares(trip, new_route, all_requests)
    passenger_fare = all_fares.get(ride_request.id, 0.0)

    return round(detour, 2), round(passenger_fare, 2)

def find_matching_trips(pickup_node_id, drop_node_id):
    matches = []

    # ← include both SCHEDULED and ACTIVE trips
    active_trips = Trip.objects.filter(
        status__in=['SCHEDULED', 'ACTIVE'],   # ← key change
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