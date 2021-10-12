from RAPTOR.raptor_functions import *


def hypraptor(SOURCE, DESTINATION, D_TIME, MAX_TRANSFER, WALKING_FROM_SOURCE, CHANGE_TIME_SEC, PRINT_PARA, stop_out,
              route_groups, routes_by_stop_dict, stops_dict, stoptimes_dict, footpath_dict):
    """
    Standard HypRaptor implementation
    Args:
        SOURCE (int): stop-id DESTINATION stop
        DESTINATION (int): stop-id SOURCE stop
        D_TIME (pandas.datetime): Departure time
        MAX_TRANSFER (int): Max transfer limit
        WALKING_FROM_SOURCE (int): 1 or 0. 1 means walking from SOURCE is allowed.
        CHANGE_TIME_SEC (int): Change time in seconds
        PRINT_PARA (int): 1 or 0. 1 means print complete path
        stop_out (dict) : key: stop-id (int), value: stop-cell id (int).
        Note: if stop-cell id of -1 denotes cut stop.
        route_groups (dict): key: tuple of all possible combinations of stop cell id,
        value: set of route ids belonging to the stop cell combination
        routes_by_stop_dict (dict): Pre-processed dict- format {stop_id: [routes]}
        stops_dict (dict): Pre-processed dict- format {route_id: [stops]}
        stoptimes_dict (dict): Pre-processed dict- format {route_id: [[trip_1], [trip_2]]}
        footpath_dict (dict): Pre-processed dict- format {from_stop_id: [(to_stop_id, footpath_time)]}
    Returns:
        out (list): List of pareto-optimal arrival Timestamps
    """
    out = []
    # Intilization
    reduced_routes = route_groups[tuple(sorted((stop_out[SOURCE], stop_out[DESTINATION])))]

    marked_stop, label, pi_label, star_label, inf_time = initlize_raptor(routes_by_stop_dict, SOURCE, MAX_TRANSFER)
    change_time = pd.to_timedelta(CHANGE_TIME_SEC, unit='seconds')
    (label[0][SOURCE], star_label[SOURCE]) = (D_TIME, D_TIME)
    Q = {}
    if WALKING_FROM_SOURCE == 1:
        try:
            trans_info = footpath_dict[SOURCE]
            for i in trans_info:
                (p_dash, to_pdash_time) = i
                label[0][p_dash] = D_TIME + to_pdash_time
                star_label[p_dash] = D_TIME + to_pdash_time
                pi_label[0][p_dash] = ('walking', SOURCE, p_dash, to_pdash_time, D_TIME + to_pdash_time)
                marked_stop.append(p_dash)
        except KeyError:
            pass
    # Main Code
    # Main code part 1
    for k in range(1, MAX_TRANSFER + 1):
        Q.clear()  # Format of Q is {route:stop}
        marked_stop = list(set(marked_stop))
        while marked_stop:
            p = marked_stop.pop()
            try:
                routes_serving_p = routes_by_stop_dict[p]
                for route in routes_serving_p:
                    if route not in reduced_routes: continue
                    stp_idx = stops_dict[route].index(p)
                    if route in Q.keys() and Q[route] != stp_idx:
                        Q[route] = min(stp_idx, Q[route])
                    else:
                        Q[route] = stp_idx
            except KeyError:
                continue
        # Main code part 2
        for route, current_stopindex_by_route in Q.items():
            current_trip_t = -1
            for p_i in stops_dict[route][current_stopindex_by_route:]:
                if current_trip_t != -1 and current_trip_t[current_stopindex_by_route][1] < min(star_label[p_i],
                                                                                                star_label[
                                                                                                    DESTINATION]):
                    arr_by_t_at_pi = current_trip_t[current_stopindex_by_route][1]
                    label[k][p_i], star_label[p_i] = arr_by_t_at_pi, arr_by_t_at_pi
                    pi_label[k][p_i] = (boarding_time, borading_point, p_i, arr_by_t_at_pi, tid)
                    marked_stop.append(p_i)
                if current_trip_t == -1 or label[k - 1][p_i] + change_time < \
                        current_trip_t[current_stopindex_by_route][1]:
                    tid, current_trip_t = get_latest_trip_new(stoptimes_dict, route, label[k - 1][p_i],
                                                              current_stopindex_by_route, change_time)
                    if current_trip_t == -1:
                        boarding_time, borading_point = -1, -1
                    else:
                        borading_point = p_i
                        boarding_time = current_trip_t[current_stopindex_by_route][1]
                current_stopindex_by_route = current_stopindex_by_route + 1
        # Main code part 3
        marked_stop_copy = [*marked_stop]
        for p in marked_stop_copy:
            try:
                trans_info = footpath_dict[p]
                for i in trans_info:
                    (p_dash, to_pdash_time) = i
                    new_p_dash_time = label[k][p] + to_pdash_time
                    if (label[k][p_dash] > new_p_dash_time) and new_p_dash_time < min(star_label[p_dash],
                                                                                      star_label[DESTINATION]):
                        label[k][p_dash], star_label[p_dash] = new_p_dash_time, new_p_dash_time
                        pi_label[k][p_dash] = ('walking', p, p_dash, to_pdash_time, new_p_dash_time)
                        marked_stop.append(p_dash)
            except KeyError:
                continue
        # Main code End
        if marked_stop == deque([]):
            #            print('code ended with termination condition')
            break
    _, _, rap_out = post_processing(DESTINATION, pi_label, PRINT_PARA, label)
    out.append(rap_out)
    return out