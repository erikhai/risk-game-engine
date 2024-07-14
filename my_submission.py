from collections import defaultdict, deque
import random
import sys
import math
from typing import Optional, Tuple, Union, cast
from risk_helper.game import Game
from risk_shared.models.card_model import CardModel
from risk_shared.queries.query_attack import QueryAttack
from risk_shared.queries.query_claim_territory import QueryClaimTerritory
from risk_shared.queries.query_defend import QueryDefend
from risk_shared.queries.query_distribute_troops import QueryDistributeTroops
from risk_shared.queries.query_fortify import QueryFortify
from risk_shared.queries.query_place_initial_troop import QueryPlaceInitialTroop
from risk_shared.queries.query_redeem_cards import QueryRedeemCards
from risk_shared.queries.query_troops_after_attack import QueryTroopsAfterAttack
from risk_shared.queries.query_type import QueryType
from risk_shared.records.moves.move_attack import MoveAttack
from risk_shared.records.moves.move_attack_pass import MoveAttackPass
from risk_shared.records.moves.move_claim_territory import MoveClaimTerritory
from risk_shared.records.moves.move_defend import MoveDefend
from risk_shared.records.moves.move_distribute_troops import MoveDistributeTroops
from risk_shared.records.moves.move_fortify import MoveFortify
from risk_shared.records.moves.move_fortify_pass import MoveFortifyPass
from risk_shared.records.moves.move_place_initial_troop import MovePlaceInitialTroop
from risk_shared.records.moves.move_redeem_cards import MoveRedeemCards
from risk_shared.records.moves.move_troops_after_attack import MoveTroopsAfterAttack
from risk_shared.records.record_attack import RecordAttack
from risk_shared.records.types.move_type import MoveType

global expansiion_point
expansion_point = None

global next_terr
next_terr = 0

# We will store our enemy in the bot state.
class BotState():
    def __init__(self):
        self.enemy: Optional[int] = None


def main():
    
    # Get the game object, which will connect you to the engine and
    # track the state of the game.
    game = Game()
    bot_state = BotState()
   
    # Respond to the engine's queries with your moves.
    while True:

        # Get the engine's query (this will block until you receive a query).
        query = game.get_next_query()

        # Based on the type of query, respond with the correct move.
        def choose_move(query: QueryType) -> MoveType:
            match query:
                case QueryClaimTerritory() as q:
                    return handle_claim_territory(game, bot_state, q)

                case QueryPlaceInitialTroop() as q:
                    return handle_place_initial_troop(game, bot_state, q)

                case QueryRedeemCards() as q:
                    return handle_redeem_cards(game, bot_state, q)

                case QueryDistributeTroops() as q:
                    return handle_distribute_troops(game, bot_state, q)

                case QueryAttack() as q:
                    return handle_attack(game, bot_state, q)

                case QueryTroopsAfterAttack() as q:
                    return handle_troops_after_attack(game, bot_state, q)

                case QueryDefend() as q:
                    return handle_defend(game, bot_state, q)

                case QueryFortify() as q:
                    return handle_fortify(game, bot_state, q)
        
        # Send the move to the engine.
        game.send_move(choose_move(query))

########### Helper Methods for Claim Territory ##########
# Have a Helper Method which returns all empty continents
def get_all_empty_continents(game: Game):
    # Get All Continents
    all_continents = game.state.map.get_continents()
    empty_conitnents = []
    for Continent in all_continents:
        terriorities_in_continent = all_continents[Continent]
        size = len(terriorities_in_continent)
        count = 0
        for Territory in terriorities_in_continent:
            occupied = game.state.territories.get(Territory).occupier
            if(occupied == None):
                count += 1
        if(count == size):
            empty_conitnents.append(Continent)
    return empty_conitnents


## Have a Helper Method which returns the best possible first territory ##
def get_best_first_placement(game: Game, Continent):
    # Get All Continents
    all_continents = game.state.map.get_continents()

    # Get All Territories in Continent
    terriorities_in_continent = all_continents[Continent]
    for Territory in terriorities_in_continent:
        occupied = game.state.territories.get(Territory).occupier
        # If we have successfully found a border we will choose that territory
        if(check_if_border(game,Territory)==True and occupied == None):
            return Territory
        
    # Iterate through each territory but this time just to get an empty space
    for Territory in terriorities_in_continent:
        occupied = game.state.territories.get(Territory).occupier
        if(occupied == None):
            #Otherwise if no border is present just return a territory
            return Territory

#Have a Method to Find the % of Empty Land in a Continent
def get_empty_land_percentage(game: Game, Continent):
    # Get All Continents
    all_continents = game.state.map.get_continents()
    territories = all_continents[Continent]
    count = 0
    for Territory in territories:
        occupied = game.state.territories.get(Territory).occupier
        if(occupied == None):
            count += 1
    return (count/len(territories))

#Have a Method which returns the Number of Continents are in
def get_continents_in(game: Game):
    cont = set()
    # Have all the terriorities we own
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    for Territory in my_territories:
        # Get the Continent 
        Continent = get_continent_from_territory(game, Territory)
        cont.add(Continent)
    # Return the length of the set
    print(len(cont),flush=True)
    return len(cont)

def handle_place_initial_troop(game: Game, bot_state: BotState, query: QueryPlaceInitialTroop) -> MovePlaceInitialTroop:
    """After all the territories have been claimed, you can place a single troop on one
    of your territories each turn until each player runs out of troops."""
    global expansion_point
    points = get_expansion_points_initially(game)
    border_territories = game.state.get_all_border_territories(game.state.get_territories_owned_by(game.state.me.player_id))
    our_continent = []
    all_continents = game.state.map.get_continents()
    for Continent, Territories in all_continents.items():
        owned_in_continent = 0
            # Iterate through each Terriotory in the Continent
        for Territory in Territories:
            size = len(Territories)
                # See occupied
            occupied = game.state.territories.get(Territory).occupier
                # If the terriority is owned by us
            if(occupied == game.state.me.player_id):
                    #increment the number of continents
                owned_in_continent += 1
            # Now see if we have more that 60% of land if so then we append it to continents with greater than sixty which we capture
        if(owned_in_continent > size * 0.9):
            our_continent.append(Continent)
    if our_continent is not None:
        print("entered", flush = True)
        random.shuffle(our_continent)
        for Continent in our_continent:
            territories = all_continents[Continent]
            random.shuffle(territories)
                # Iterate through each terriority in the Continent we can claim
            for Terriority in territories:
                occupied = game.state.territories.get(Terriority).occupier
                    # If we own a border terriority 
                if occupied == game.state.me.player_id and Territory in border_territories:
                    number_of_border_troops = game.state.territories[Terriority].troops
                    if number_of_border_troops < 3:
                        return game.move_place_initial_troop(query, Terriority) 
                elif occupied == game.state.me.player_id:
                    number_of_border_troops = game.state.territories[Terriority].troops
                    if number_of_border_troops < 2:
                        return game.move_place_initial_troop(query, Terriority) 
    if(len(points)==1):
        for Point in points:
            return game.move_place_initial_troop(query, Point) 
        
    elif len(points)==0:
        border_territories = game.state.get_all_border_territories(game.state.get_territories_owned_by(game.state.me.player_id))
        # We will place a troop in the border territory with the least troops currently
        # # on it. This should give us close to an equal distribution.
        border_territory_models = [game.state.territories[x] for x in border_territories]
        min_troops_territory = min(border_territory_models, key=lambda x: x.troops)
        return game.move_place_initial_troop(query, min_troops_territory.territory_id)
    else:
        global next_terr
        Point_Values = []
        # We will make sure it is evenly distributed between expansion points
        for Point in points:
            Point_Values.append(Point)
        if(next_terr > len(Point_Values)-1):
            next_terr = 0
            print(f'The length  of Point Values is {len(Point_Values)}')
            return game.move_place_initial_troop(query, Point_Values[len(Point_Values)-1]) 
        else:
            next_terr += 1
            return game.move_place_initial_troop(query, Point_Values[next_terr-1])

def handle_claim_territory(game: Game, bot_state: BotState, query: QueryPlaceInitialTroop) -> MoveClaimTerritory:
    """After all the territories have been claimed, you can place a single troop on one
    of your territories in each turn until each player runs out of troops."""
    # Iterate through every continent
    # Have all the terriorities we own
    global expansion_point
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    # Get All Continents
    all_continents = game.state.map.get_continents()
    # Get All Adjacent Territories
    adjacent_territories = game.state.get_all_adjacent_territories(my_territories)
    # If we have not choosen any territory
    if(len(my_territories)==0):
        # Then we want to select the border of the smallest-possible-emptiest continent
        # Find all the emptiest continents
        all_empty_continets = get_all_empty_continents(game)
        # Now find the smallest continent out of all of them
        smallest_continent = all_empty_continets[0]
        territories_of_smallest = all_continents[smallest_continent]
        smallest_continent_size = len(territories_of_smallest)
        #Iterate through every continent and find the smallest continent
        for Continent in all_empty_continets:
            terriorities_in_continent = all_continents[Continent]
            if(len(terriorities_in_continent) < smallest_continent_size ):
                smallest_continent = Continent
                smallest_continent_size = len(terriorities_in_continent)
        # Now that we have iterated we will select border territory if available in the continent
        print(smallest_continent, flush=True)
        territory_choice = get_best_first_placement(game,smallest_continent)
        print(territory_choice, flush=True)
        return game.move_claim_territory(query, territory_choice)
    # Otherwise if we are not in our first move
    else:
        # Iterate through each territories we own
        for Territory in my_territories:
            # First see if we have a border territory 
            # If we have a border territory let us take a bit of another continent adjacent to the territory if it still can be conquered
            # Only do this to secure the two beginning continents
            if(check_if_border(game,Territory)==True and len(my_territories)==1):
                # Get The Adjacent Territory to the Border we have claimed
                adj_territories = game.state.get_all_adjacent_territories([Territory])
                for AdjTerr in adj_territories:
                    occupied = game.state.territories.get(AdjTerr).occupier
                    adj_terr_cont = get_continent_from_territory(game,AdjTerr)
                    curr_cont = get_continent_from_territory(game, Territory)
                    if(curr_cont != adj_terr_cont and occupied == None ):
                        expansion_point = AdjTerr
                        return game.move_claim_territory(query, AdjTerr)
        # If we cannot find a strategic border move like that we will iterate through our territories and choose an empty unoccupied territory
        # First Case is Adjacent in the Territory with the highest % Continent
        best_choice_territory = None
        continent_ownership = 0
        for Territory in adjacent_territories:
            Cont_From = get_continent_from_territory(game,Territory)
            Percentage_Ownership = get_percentage_ownership_in_continent(game,Cont_From)
            # See if there is any un-occupied empty territories which are adjacent
            occupied = game.state.territories.get(Territory).occupier
            if(occupied == None):
                if(Percentage_Ownership > continent_ownership):
                    best_choice_territory = Territory
                    continent_ownership = Percentage_Ownership
        # If we find the best continent to choose from
        if(best_choice_territory != None):
            # Claim the territory
            return game.move_claim_territory(query, best_choice_territory)
        # Any adjacent territory will  be ok if we cannot find a continent to take over adjacently
        for Territory in adjacent_territories:
            # See if there is any un-occupied empty territories which are adjacent
            occupied = game.state.territories.get(Territory).occupier
            if(occupied== None):
                return game.move_claim_territory(query, Territory)
        # If we could not find any suitable adjacent territories then we just choose a random unclaimed peice of land
        for Continent, Terriorities in all_continents.items():
            for Terrritory in Terriorities:
                occupied = game.state.territories.get(Terrritory).occupier
                if(occupied == None):
                    return game.move_claim_territory(query, Terrritory)


def handle_distribute_troops(game: Game, bot_state: BotState, query: QueryDistributeTroops) -> MoveDistributeTroops:
    """After you redeem cards (you may have chosen to not redeem any), you need to distribute
    all the troops you have available across your territories. This can happen at the start of
    your turn or after killing another player.
    """
    expansion_points = set()
    # Get Every Continent we have and its information
    all_continents_dict = {}
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    # Get Continents we have the highest control over
    # Get All Continents
    all_continents = game.state.map.get_continents()
    # Store the Continent we will Attack
    continent_to_attack = None
    # Iterate through each continent
    for Continent in all_continents:
        # If we have fully owned a continent then add it to the dictionary
        all_continents_dict[Continent] = get_percentage_ownership_in_continent(game, Continent)
    # Now we want to sort
    sorted_continents = dict(sorted(all_continents_dict.items(), key=lambda val:val[1], reverse=True))
    for Continent in sorted_continents:
        # If we do not have a completed continent
        if sorted_continents[Continent] != 1:
            # This will be the continent where we attack
            continent_to_attack = Continent
            # Then take the majority continent we have
            # Select Territories we have adjacent to enemy territory in the continent
            points = get_adjacent_territories_to_enemy(game, Continent)
            # Add All the Points
            for Point in points:
                expansion_points.add(Point)
            if(len(expansion_points) > 0):
                break
            else:
                continent_to_attack = None
        else:
            # If we have a Continent Secured 
            # See if we have any Connected Expansion Points
            # First get Bordering Territory 
            # First get the Connected Continents
            adj_continents = get_adj_continents(game, Continent)
            print(f'Adj Continents: {adj_continents}', flush=True)
            bordering_terr = get_bordering_continent_territory(game, Continent)
            for BorderTerr in bordering_terr:
                if check_if_border_adj_enemy(game, BorderTerr) == True:
                    expansion_points.add(BorderTerr)
                # If we have allies in the border
                else:
                    # Add the Border in the adjacent Continent we own and then calculate the expansion points
                    if check_if_next_border_is_ours(game, BorderTerr) != None:
                        Points = find_expansion_point(game, check_if_next_border_is_ours(game, BorderTerr))
                        for Point in Points:
                            expansion_points.add(Point)
                    else:
                        # Get the continents adjacent to the territory
                        # Add to Expansion Point if we do not own next border
                        expansion_points.add(BorderTerr)
            # If we did not find any connected continent then choose a continent to expand too
    points = list(expansion_points)
    if len(points) == 0:
        points = game.state.get_territories_owned_by(game.state.me.player_id)
    # We will distribute troops across our border territories.
    total_troops = game.state.me.troops_remaining
    distributions = defaultdict(lambda: 0)
    border_territories = game.state.get_all_border_territories(
        game.state.get_territories_owned_by(game.state.me.player_id)
    )
    # We need to remember we have to place our matching territory bonus
    # if we have one.
    if len(game.state.me.must_place_territory_bonus) != 0:
        assert total_troops >= 2
        distributions[game.state.me.must_place_territory_bonus[0]] += 2
        total_troops -= 2

    # We will equally distribute across border territories in the early game,
    # but start doomstacking in the late game.
    if len(game.state.recording) > 0:
        our_collection = []
        for i in range(total_troops):
            print(f'Distribution {our_collection}', flush=True)
            count = sys.maxsize
            min_terr = None
            for terr in points:
                check = False
                counter = 0
                for group in our_collection:
                    if group[0] == terr:
                        print(f'We found {terr}', flush=True)
                        counter = group[1]
                        print(f'Counter is {counter}', flush=True)
                        check = True
                        
                        break
                if check == False:
                    if game.state.territories[terr].troops< count:
                        
                        count = game.state.territories[terr].troops
                        min_terr = terr
                        print(f'The newly found minterr is {min_terr} ', flush=True)
                else:
                    if game.state.territories[terr].troops + counter < count:
                        count = game.state.territories[terr].troops + counter
                        min_terr = terr
                        print(f'The oldy found minterr is {min_terr} ', flush=True)
                print(f'Count is {count}', flush=True)
            if min_terr is not None:
                distributions[min_terr] += 1
                if len(our_collection) == 0:
                    our_collection.append([min_terr, 1])
                else:
                    check = False
                    for group in our_collection:
                        if group[0] == min_terr:
                            group[1] = group[1] + 1
                            check = True
                            
                            break
                    if check == False:
                        our_collection.append([min_terr, 1])
    return game.move_distribute_troops(query, distributions)


def handle_redeem_cards(game: Game, bot_state: BotState, query: QueryRedeemCards) -> MoveRedeemCards:
    """After the claiming and placing initial troops phases are over, you can redeem any
    cards you have at the start of each turn, or after killing another player."""

    # We will always redeem the minimum number of card sets we can until the 12th card set has been redeemed.
    # This is just an arbitrary choice to try and save our cards for the late game.

    # We always have to redeem enough cards to reduce our card count below five.
    card_sets: list[Tuple[CardModel, CardModel, CardModel]] = []
    cards_remaining = game.state.me.cards.copy()

    while len(cards_remaining) >= 5:
        card_set = game.state.get_card_set(cards_remaining)
        # According to the pigeonhole principle, we should always be able to make a set
        # of cards if we have at least 5 cards.
        assert card_set != None
        card_sets.append(card_set)
        cards_remaining = [card for card in cards_remaining if card not in card_set]

    # Remember we can't redeem any more than the required number of card sets if 
    # we have just eliminated a player.
    if game.state.card_sets_redeemed > 0 and query.cause == "turn_started":
        card_set = game.state.get_card_set(cards_remaining)
        while card_set != None:
            card_sets.append(card_set)
            cards_remaining = [card for card in cards_remaining if card not in card_set]
            card_set = game.state.get_card_set(cards_remaining)

    return game.move_redeem_cards(query, [(x[0].card_id, x[1].card_id, x[2].card_id) for x in card_sets])


############        Have a bunch of helper methods for handle_attack      #############
# Have a method which gives us the percentage ownership we have in a specific continent

# Have a method which gets the percentage of ownership we have in a continent
def get_percentage_ownership_in_continent(game: Game, Continent) -> float:
    # Get All Continents
    all_continents = game.state.map.get_continents()
    terriorities_in_continent = all_continents[Continent]
    territories_claimed = 0
    for Territory in terriorities_in_continent:
        occupied = game.state.territories.get(Territory).occupier
        # If we own the territory increment the count
        if occupied == game.state.me.player_id:
            territories_claimed += 1
    return territories_claimed/len(terriorities_in_continent)

# Have another method which returns the highest number of enemy troops adjacent to a Territory
def get_enemy_troops_adjacent(game: Game, Territory) -> int:
    num_enemy_troops = 0
    adj_territories = game.state.get_all_adjacent_territories([Territory])
    for AdjTerritories in adj_territories:
        # Now see if the territory is occupied by the enemy
        occupied = game.state.territories.get(AdjTerritories).occupier
        if occupied !=  game.state.me.player_id:
            # Add it to the number of enemy troops
            num_enemy_troops += game.state.territories[AdjTerritories].troops
    # Now return the number of enemy troops
    return num_enemy_troops

# We want a method to get number of ally troops surronding an enemy terriotry
def get_ally_troops(game: Game, Territory) -> int:
    num_ally_troops = 0
    adj_territories = game.state.get_all_adjacent_territories([Territory])
    # Iterate through each territory
    for AdjTerritories in adj_territories:
        # Now see if the territory is occupied by us
        occupied = game.state.territories.get(AdjTerritories).occupier
        if occupied == game.state.me.player_id:
            # Add it by the number of troops we have
            num_ally_troops += game.state.territories[AdjTerritories].troops
    # Now return the number of ally troops
    return num_ally_troops

# Given a territory we want to find what Continent it is from
def get_continent_from_territory(game: Game, Territory):
    # Iterate through each continent
    all_continents = game.state.map.get_continents()
    for Continent, Terriorities in all_continents.items():
        for Territoriy in Terriorities:
            # If we found the Continent with the territory return the Continent
            if Territoriy == Territory:
                return Continent
    # If we found no matching continent return None
    return None

# Given a Continent calculate how many troops we have in that continent
def get_troops_given_continent(game: Game, Continent):
    # Iterate through each continent
    all_continents = game.state.map.get_continents()
    territories = all_continents[Continent]
    troop_count = 0
    for Territory in territories:
        # Now see if the territory is occupied by us
        occupied = game.state.territories.get(Territory).occupier
        if occupied == game.state.me.player_id: 
            # If it is add it to the troop count
            troop_count = troop_count + game.state.territories[Territory].troops
    return troop_count

# Given A Continent extra the information of enemies 
def get_enemy_information(game: Game, Continent):
    return None

# Given a Continent return all the weak Territories
def get_weak_territories_of_enemy(game: Game, Continent):
    weak_territories = []
    all_continents = game.state.map.get_continents()
    territories = all_continents[Continent]
    for Territory in territories:
        # See if is enemy territory 
        occupied = game.state.territories.get(Territory).occupier
        # If a territory has one troop occupied in it it will be considered weak
        if occupied != game.state.me.player_id and game.state.territories[Territory].troops == 1:
            weak_territories.append(Territory)
    return weak_territories

# Given a territory get the most weakest adjacent territory to attack
def get_weakest_adjcent_enemy_territory(game: Game, Territory):
    # Have a list of bordering terriotiries 
    bordering_territories = game.state.get_all_adjacent_territories([Territory])
    weakest_territory = None
    weakest_troop_count = float('inf')
    for AdjTerr in bordering_territories:
        # See if it is enemy
        occupied = game.state.territories.get(AdjTerr).occupier
        # If it is enemy find the weakest adjacent one to attack
        if occupied != game.state.me.player_id and game.state.territories[AdjTerr].troops < weakest_troop_count:
            weakest_territory = AdjTerr
            weakest_troop_count = game.state.territories[AdjTerr].troops
    return weakest_territory

# Given a Continent find the weak and vulnerable territories we can attack
def get_vulnerable_territories(game: Game, Continent):
    vulnerable_territories = []


# Have a Method which will calculate how conquerable a continent is
def calculate_how_conquerable_continent_is(game: Game, Continent):
    pass

# Have a Method which gets the adjacent Continent to a given Continent
def get_adj_continents(game: Game, Continent):
    adj_continents = set()
    all_continents = game.state.map.get_continents()
    territories = all_continents[Continent]
    # Iterate through every territory
    for Territory in territories:
        # Get the Adjacent Land to the Territory
        AdjTerr = game.state.get_all_adjacent_territories([Territory])
        for AdjTerritories in AdjTerr:
            if get_continent_from_territory(game, AdjTerritories) != Continent:
                adj_continents.add(get_continent_from_territory(game,AdjTerritories))
    # Return the adj continents
    return adj_continents

# Have a Method which gets expansion points given Continent
def get_expansion_point(game: Game, Continent):
    expansion_points = []
    # Have all the terriorities we own
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    # Get All Continents
    all_continents = game.state.map.get_continents()
    terr_in_continent = all_continents[Continent]
    for Territiory in terr_in_continent:
        AdjTerr = game.state.get_all_adjacent_territories([Territiory])
        for AdjT in AdjTerr:
            if AdjT not in my_territories and get_continent_from_territory(game,AdjT) == Continent:
                expansion_points.append(Territiory)
    # Return the Expansion Points
    return expansion_points

    
def expansion_code_test(game: Game):
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    for Terr in my_territories:
        if check_if_border(game,Terr) == True:
            find_expansion_point(game, Terr)


def get_expansion_points_initially(game: Game):
    # Store all the expansion points
    expansion_points = set()
    # Get All Continents
    # The Next Priority is fortfying so we can expand and conquer a continent
    all_owned_continents = {}
    all_continents_dict = {}
    # Get All Continents
    all_continents = game.state.map.get_continents()
    # Iterate through each continent
    for Continent in all_continents:
        # If we have fully owned a continent then add it to the dictionary
        if(get_percentage_ownership_in_continent(game, Continent) == 1):
            # Store it in a dictionary # Set the Value to the Number of Troops we have stationed in the continent
            all_owned_continents[Continent] = get_troops_given_continent(game, Continent)
        all_continents_dict[Continent] = get_percentage_ownership_in_continent(game, Continent)
        print(f'Continent {Continent} Percentage: {all_continents_dict[Continent]}')
    # For the First Case See if we Own a Continent or more than one
    if(len(all_owned_continents) > 0):
        # Iterate through each continent
        owned_continent = None
        for Continent in all_owned_continents:
            owned_continent = Continent
            break
        # Now we have the Continent
        bordering = get_bordering_continent_territory(game, owned_continent)
        continents = get_adj_continents(game, owned_continent)
        # Now iterate through each border
        for Territory in bordering:
            # See if we occupy the land in the bordering territory 
            if(check_if_next_border_is_ours(game, Territory)!= None and check_if_border_adj_enemy(game, Territory)==False):
                print(f'{check_if_next_border_is_ours(game, Territory)}', flush=True)
                points = find_expansion_point(game, check_if_next_border_is_ours(game, Territory))
                for Point in points:
                    expansion_points.add(Point)
            else:
                expansion_points.add(Territory)
        return expansion_points
    else:
        cond = False
        # If we do not own a continent
        # Find the Continent where we have the most territory and make them our expansion points
        # First sort it based on incresing ownership %
        sorted_continents = dict(sorted(all_continents_dict.items(), key=lambda val:val[1], reverse=True))
        print(sorted_continents)
        my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
        for Continent in sorted_continents:
            # If we have majority of the continent
            # See if we can conquer more than half a continent
            if(sorted_continents[Continent] >= 0.5):
                # See if there is any adjacent enemy territory in the continent
                # Get the Borders
                bordering = get_bordering_continent_territory(game, Continent)
                adj_terr_to_enemies = get_adjacent_territories_to_enemy(game, Continent)
                # If there is adjacent territory to the enemy
                if(len(adj_terr_to_enemies)!=0):
                    for Territory in adj_terr_to_enemies:
                        # If it any neighbouring territories
                        expansion_points.add(Territory)
                    return expansion_points
                # If there is none adjacent to the enemy just select random territory in the contiinent which we own
                else:
                    territories = all_continents[Continent]
                    for Territory in territories:
                        if Territory in my_territories:
                            expansion_points.add(Territory)
                    return expansion_points
            # Randomly Select
            else:
                territories = all_continents[Continent]
                for Territory in territories:
                    if Territory in my_territories:
                        expansion_points.add(Territory)
                    return expansion_points
    return expansion_points

# Haave a Method which retrives all expansion points if we have a majority continent
def get_adjacent_territories_to_enemy(game: Game, Continent):
    territories = set()
    # Get All Continents
    all_continents = game.state.map.get_continents()
    curr_continent = Continent
    # Get the Territories in the Continent
    territories_in_continent = all_continents[curr_continent]
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    for Territory in territories_in_continent:
        # Get Adjacent Territories
        adjacent = game.state.get_all_adjacent_territories([Territory])
        for AdjTerritory in adjacent:
            # Find All Enemy Territories Around Us
            if Territory in my_territories and AdjTerritory not in my_territories:
                territories.add(Territory)
    return territories

# Have a Method which gets bordering / continent territotories given Continent
def get_bordering_continent_territory(game: Game, Continent):
    Border = set()
    # Get All the Continents 
    all_continents = game.state.map.get_continents()
    territories = all_continents[Continent]
    for Terr in territories:
        AdjTerr = game.state.get_all_adjacent_territories([Terr])
        # If the Adjacent Territory is not in the same continent then it is the land we are looking for
        for AdjT in AdjTerr:
            if get_continent_from_territory(game,AdjT) != Continent:
                Border.add(Terr)
    return Border

def check_if_border_adj_enemy(game: Game, Territory):
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    AdjT = game.state.get_all_adjacent_territories([Territory])
    curr_cont = get_continent_from_territory(game, Territory)
    for Adj in AdjT:
        if(Adj not in my_territories and curr_cont != get_continent_from_territory(game,Adj)):
            return True
    return False


def check_if_next_border_is_ours(game: Game, Territory):
    adj_border_terr = game.state.get_all_adjacent_territories([Territory])
    curr_continent = get_continent_from_territory(game, Territory)
    continents = get_adj_continents(game,get_continent_from_territory(game, Territory))
    for Terr in adj_border_terr:
        occupied = game.state.territories.get(Terr).occupier
        if(occupied == game.state.me.player_id and curr_continent != get_continent_from_territory(game, Terr)):
            return Terr
    return None

def get_border_continents_from_terr(game: Game, Territory):
    conts = set()
    curr_continent = get_continent_from_territory(game, Territory)
    adjT = game.state.get_all_adjacent_territories([Territory])
    for adj in adjT:
        if get_continent_from_territory(game,adj) != curr_continent:
            conts.add(adj)
    return conts

def get_continent_to_attack(game):
    # Have a List of all Full Continents
    all_full = []
    # Get Every Continent we have and its information
    all_continents_dict = {}
    # Get Every Continent we have and its information
    all_continents = game.state.map.get_continents()
    # Iterate through each continent
    for Continent in all_continents:
        if(get_percentage_ownership_in_continent(game, Continent)==1):
            all_full.append(Continent)
    # Now we have a dictionary of non full continents
    for Continent in all_continents:
        if Continent not in all_full:
            # If we have fully owned a continent then add it to the dictionary
            all_continents_dict[Continent] = get_percentage_ownership_in_continent(game, Continent)
    # Now we want to sort
    sorted_continents = dict(sorted(all_continents_dict.items(), key=lambda val:val[1], reverse=True))
    if(len(all_full)==0):
        for Cont in sorted_continents:
            return [Cont]
    else:
        Conts = []
        for Continent in sorted_continents:
            Adj_Cont = get_adj_continents(game,Continent)
            for AdjCont in Adj_Cont:
                if AdjCont in all_full:
                    return Continent
        for Continent in sorted_continents:
            return Continent
        

# Get Continents which we have majority of distribution
def get_majority_continents(game):
    # Get Every Continent we have and its information
    all_continents_dict = {}
    # Get Every Continent we have and its information
    all_continents = game.state.map.get_continents()
    for Continent in all_continents:
        if get_percentage_ownership_in_continent(game, Continent) != 1:
            # If we have fully owned a continent then add it to the dictionary
            all_continents_dict[Continent] = get_percentage_ownership_in_continent(game, Continent)
    # Now we want to sort
    sorted_continents = dict(sorted(all_continents_dict.items(), key=lambda val:val[1], reverse=True))
    for Continent in sorted_continents:
        return Continent


# See if we claimed continent after attack if we do 
    
# Have a Method which will attack the enemy
# Have a Method which will use analytics to determine a vulnerable enemy to attack and with what territory
# See if we claimed continent after attack if we do 
    
# Have a Method which will attack the enemy
# Have a Method which will use analytics to determine a vulnerable enemy to attack and with what territory
# Have a Method which will attack the enemy
# Have a Method which will use analytics to determine a vulnerable enemy to attack and with what territory
def handle_attack(game: Game, bot_state: BotState, query: QueryAttack) -> Union[MoveAttack, MoveAttackPass]:
    """After the troop phase of your turn, you may attack any number of times until you decide to
    stop attacking (by passing). After a successful attack, you may move troops into the conquered
    territory. If you eliminated a player you will get a move to redeem cards and then distribute troops."""
    # Have all the terriorities we own
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    # First we want to see if we can conduct an attack to capture a continent if we nearly have it
    for Territory in my_territories:
        # Get the Continent the Territory is From
        Territory_Continent = get_continent_from_territory(game, Territory)
        # Now view all potential adjacent territories to the current Territory as potential to be attacked
        Adjacent_Territories = game.state.get_all_adjacent_territories([Territory])
        # Now iterate through all Adjacent Territories
        # Select the best Adjacent Territory to Attack
        Priority_Terr = []
        Majority = get_majority_continents(game)
        for AdjTerr in Adjacent_Territories:
            occupied = game.state.territories.get(AdjTerr).occupier
            # If we have encountered an enemy territory
            if occupied != game.state.me.player_id:
                if get_continent_from_territory(game,AdjTerr) == Majority:
                    Priority_Terr.append(AdjTerr)
        # Now see if we have any priority terr
        if(len(Priority_Terr) > 0):
            Weakest = None
            for Priority in Priority_Terr:
                if Weakest == None:
                    Weakest = Priority
                else:
                    if game.state.territories[Priority].troops < game.state.territories[Weakest].troops:
                        Weakest = Priority
            # Now Attack 
            territory_troops = game.state.territories[Territory].troops
            enemy_troops = game.state.territories[Weakest].troops
            # Get the Number of Enemy Troops in this situation
            enemy_troops_two = get_enemy_troops_adjacent(game, Weakest)
            if(territory_troops >= 500 and territory_troops > enemy_troops):
                return game.move_attack(query, Territory, Weakest, min(3, game.state.territories[Territory].troops - 1))
            else:
                if(((territory_troops > enemy_troops and territory_troops > 2) or (territory_troops > 1 and enemy_troops == 1)) and territory_troops  >= enemy_troops_two):
                    return game.move_attack(query, Territory, Weakest, min(3, game.state.territories[Territory].troops - 1))
        # Otherwise just attack
        # If we have 40% more troops at least then we are allowed to attack
        for AdjTerr in Adjacent_Territories:
            occupied = game.state.territories.get(AdjTerr).occupier
            if occupied != game.state.me.player_id:
                territory_troops = game.state.territories[Territory].troops
                # We need to consider the opposing enemy troops
                enemy_troops = game.state.territories[AdjTerr].troops
                # See if we should attack it
                # # # # See if we should also attack if we are in a border
                # Get the Number of Enemy Troops in this situation
                enemy_troops_two = get_enemy_troops_adjacent(game, AdjTerr)
                if(territory_troops >= 500 and territory_troops > enemy_troops):
                    return game.move_attack(query, Territory, AdjTerr, min(3, game.state.territories[Territory].troops - 1))
                else:
                    if(((territory_troops > enemy_troops and territory_troops > 2) or (territory_troops > 1 and enemy_troops == 1)) and territory_troops  >= enemy_troops_two):
                        return game.move_attack(query, Territory, AdjTerr, min(3, game.state.territories[Territory].troops - 1))
    # Otherwise do not attack
    return game.move_attack_pass(query)

# Have a Method to check if we are at the border
def check_if_border(game: Game, Territory):
    adjacent_territories = game.state.get_all_adjacent_territories([Territory])
    Continent = get_continent_from_territory(game,adjacent_territories[0])
    for Terr in adjacent_territories:
        Curr_Continent = get_continent_from_territory(game, Terr)
        if(Curr_Continent != Continent):
            return True
    return False

def handle_troops_after_attack(game: Game, bot_state: BotState, query: QueryTroopsAfterAttack) -> MoveTroopsAfterAttack:
    """After conquering a territory in an attack, you must move troops to the new territory."""
    # First we need to get the record that describes the attack, and then the move that specifies
    # which territory was the attacking territory.
    record_attack = cast(RecordAttack, game.state.recording[query.record_attack_id])
    move_attack = cast(MoveAttack, game.state.recording[record_attack.move_attack_id])
    # Get if we are leaving a bordering territory
    # Lets say we want to move to a border 
    # See if the old territory has any enemies around it
    old = move_attack.attacking_territory
    new = move_attack.defending_territory
    adj_old = game.state.get_all_adjacent_territories([old])
    # Have all the terriorities we own
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    enemy_nearby = False
    for adjT in adj_old:
        if adjT not in my_territories and adjT != new:
            enemy_nearby = True
    # If there are enemy nearby in the old territory 
    if(enemy_nearby):
        # Only move 30%
        troops_to_return = math.floor(game.state.territories[move_attack.attacking_territory].troops*0.9)
        if(troops_to_return <= 2):
            return game.move_troops_after_attack(query, game.state.territories[move_attack.attacking_territory].troops-1)
        else:
            return game.move_troops_after_attack(query, troops_to_return)
    else:
        # Transfer max troops
        return game.move_troops_after_attack(query, game.state.territories[move_attack.attacking_territory].troops-1)
    
def handle_defend(game: Game, bot_state: BotState, query: QueryDefend) -> MoveDefend:
    """If you are being attacked by another player, you must choose how many troops to defend with."""
    # We will always defend with the most troops that we can.
    # First we need to get the record that describes the attack we are defending against.
    # 2 troops -> 2 dice : Usually 3 3 dice
    # 1 troop -> 1 dice  : Usually 1 1 dice
    # We will always defend with the most troops that we can.
    # First we need to get the record that describes the attack we are defending against.
    move_attack = cast(MoveAttack, game.state.recording[query.move_attack_id])
    defending_territory = move_attack.defending_territory
    # We can only defend with up to 2 troops, and no more than we have stationed on the defending
    # territory.
    defending_troops = min(game.state.territories[defending_territory].troops, 2)
    return game.move_defend(query, defending_troops)
    

def handle_fortify(game: Game, bot_state: BotState, query: QueryFortify) -> Union[MoveFortify, MoveFortifyPass]:
    """At the end of your turn, after you have finished attacking, you may move a number of troops between
    any two of your territories (they must be adjacent)."""
     # Find all expansion points and sort them out weakest to strongest
     # For each expansion point, check the adjacent territories
     # If there are any adjacent territories we own check if those territories are only surrounded by territories we own
     # Take the highest adjacent territory to transfer troops into expansion point
    
    

    # Iterate through the continents we have
    expansion_points = set()
    # Get Every Continent we have and its information
    all_continents_dict = {}
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    # Get Continents we have the highest control over
    # Get All Continents
    all_continents = game.state.map.get_continents()
    # Store the Continent we will Attack
    continent_to_attack = None
    # Iterate through each continent
    for Continent in all_continents:
        # If we have fully owned a continent then add it to the dictionary
        all_continents_dict[Continent] = get_percentage_ownership_in_continent(game, Continent)
    # Now we want to sort
    sorted_continents = dict(sorted(all_continents_dict.items(), key=lambda val:val[1], reverse=True))
    for Continent in sorted_continents:
        # If we do not have a completed continent
        if sorted_continents[Continent] != 1:
            # This will be the continent where we attack
            continent_to_attack = Continent
            # Then take the majority continent we have
            # Select Territories we have adjacent to enemy territory in the continent
            points = get_adjacent_territories_to_enemy(game, Continent)
            # Add All the Points
            for Point in points:
                expansion_points.add(Point)
            if(len(expansion_points) > 0):
                break
            else:
                continent_to_attack = None
        else:
            # If we have a Continent Secured 
            # See if we have any Connected Expansion Points
            # First get Bordering Territory 
            # First get the Connected Continents
            adj_continents = get_adj_continents(game, Continent)
            print(f'Adj Continents: {adj_continents}', flush=True)
            bordering_terr = get_bordering_continent_territory(game, Continent)
            for BorderTerr in bordering_terr:
                if check_if_border_adj_enemy(game, BorderTerr) == True:
                    expansion_points.add(BorderTerr)
                # If we have allies in the border
                else:
                    # Add the Border in the adjacent Continent we own and then calculate the expansion points
                    if check_if_next_border_is_ours(game, BorderTerr) != None:
                        Points = find_expansion_point(game, check_if_next_border_is_ours(game, BorderTerr))
                        for Point in Points:
                            expansion_points.add(Point)
                    else:
                        # Get the continents adjacent to the territory
                        # Add to Expansion Point if we do not own next border
                        expansion_points.add(BorderTerr)
            # If we did not find any connected continent then choose a continent to expand too
    print(f'{expansion_points} points we have!')
    exp_list = list(expansion_points)
    length = len(exp_list)
    for i in range(length):
        # Last i elements are already in place
        for j in range(0, length-i-1):
            # Traverse the array from 0 to n-i-1
            # Swap if the element found is greater than the next element
            game.state.territories[exp_list[j]].troops
            if game.state.territories[exp_list[j]].troops > game.state.territories[exp_list[j+1]].troops:
                exp_list[j], exp_list[j+1] = exp_list[j+1], exp_list[j]
    
    the_terr = None
    best = -1
    for points in exp_list:
        adj_territory = game.state.get_all_adjacent_territories([points])
        for adj in adj_territory:
            enemy_troops = get_enemy_troops_adjacent(game, adj)
            occupied = game.state.territories.get(adj).occupier
            if enemy_troops == 0 and game.state.territories[adj].troops > 1 and occupied == game.state.me.player_id:
                if best < game.state.territories[adj].troops:
                    the_terr = adj
                    best = game.state.territories[adj].troops
            if the_terr is not None:
                return game.move_fortify(query, the_terr, points, game.state.territories[the_terr].troops - 1)
                
        
        
        
    return game.move_fortify_pass(query)

# Finds the Expansion Point given the Continent
def find_expansion_point(game: Game, initialTerr):
    # Get all Territories
    # We will use a dictionary so we do not expand the same Territories again
    terr = {}
    # Get All Continents
    all_continents = game.state.map.get_continents()
    curr_cont = get_continent_from_territory(game, initialTerr)
    # Get All Territories in continent
    get_all_terr_in_cont = all_continents[curr_cont] # type: ignore
    for territory in get_all_terr_in_cont:
        # We will set every terr value to False as we have not visited them
        terr[territory] = False
    # Now have a stack
    stack = [initialTerr]
    points = set()
    # Iterate until the stack is empty
    while(len(stack)!=0):
        # See if the territory has enemy territory around it in the same continent
        adj_terr = game.state.get_all_adjacent_territories([stack[0]])
        curr_occupied = game.state.territories.get(stack[0]).occupier
        # Set the first node to visited
        terr[stack[0]] = True
        for adjT in adj_terr:
            occupied = game.state.territories.get(adjT).occupier
            if get_continent_from_territory(game, adjT) == curr_cont and occupied == game.state.me.player_id and terr[adjT] != True and curr_occupied == game.state.me.player_id:
                stack.append(adjT)
            # Append it as an expansion point if there is enemy land near it in the same continent
            elif get_continent_from_territory(game, adjT) == curr_cont and occupied != game.state.me.player_id and terr[adjT] != True and curr_occupied == game.state.me.player_id:
                points.add(stack[0])
        # At the end of the loop just pop the first element
        stack.pop(0)
    # Return the solution points
    print(points, flush=True)
    return points

def find_expansion_point_all_continents(game: Game, initialTerr):
    # Get all Territories
    # We will use a dictionary so we do not expand the same Territories again
    terr = {}
    # Get All Continents
    all_continents = game.state.map.get_continents()
    # Get All Territories in continent
    for Continent in all_continents:
        territories = all_continents[Continent]
        for Territory in territories:
            terr[Territory] = False
    # Now have a stack
    stack = [initialTerr]
    points = set()
    # Iterate until the stack is empty
    while(len(stack)!=0):
        # See if the territory has enemy territory around it in the same continent
        adj_terr = game.state.get_all_adjacent_territories([stack[0]])
        curr_occupied = game.state.territories.get(stack[0]).occupier
        # Set the first node to visited
        terr[stack[0]] = True
        for adjT in adj_terr:
            occupied = game.state.territories.get(adjT).occupier
            if  occupied == game.state.me.player_id and terr[adjT] != True and curr_occupied == game.state.me.player_id:
                stack.append(adjT)
            # Append it as an expansion point if there is enemy land near it in the same continent
            elif occupied != game.state.me.player_id and terr[adjT] != True and curr_occupied == game.state.me.player_id:
                points.add(stack[0])
        # At the end of the loop just pop the first element
        stack.pop(0)
    # Return the solution points
    print(points, flush=True)
    return points

def find_expansion_continent(game: Game, Continent):
    cont = {}
    all_continents = game.state.map.get_continents()
    for Continent in all_continents:
        cont[Continent] = False
    # Now have a stack
    stack = [Continent]
    solutions = set()
    # Iterate through the stack
    while(len(stack)!=0):
        # Get the Adjacnet Continents
        cont_adj = get_adj_continents(game, stack[0])
        # Set the first continent as visited
        cont[stack[0]] = True
        for Cont in cont_adj:
            if get_percentage_ownership_in_continent(game, Cont) != 1 and cont[Cont] != True:
                solutions.add(Cont)
            elif get_percentage_ownership_in_continent(game, Cont) == 1 and cont[Cont] != True:
                stack.append(Cont)
            stack.pop(0)
    return solutions

def find_shortest_path_from_vertex_to_set(game: Game, source: int, target_set: set[int]) -> list[int]:
    """Used in move_fortify()."""

    # We perform a BFS search from our source vertex, stopping at the first member of the target_set we find.
    queue = deque()
    queue.appendleft(source)

    current = queue.pop()
    parent = {}
    seen = {current: True}

    while len(queue) != 0:
        if current in target_set:
            break

        for neighbour in game.state.map.get_adjacent_to(current):
            if neighbour not in seen:
                seen[neighbour] = True
                parent[neighbour] = current
                queue.appendleft(neighbour)

        current = queue.pop()

    path = []
    while current in parent:
        path.append(current)
        current = parent[current]

    return path[::-1]

if __name__ == "__main__":
    main()
