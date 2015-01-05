
from .bet import Bet

POINT_CHIP_LOC = {
    '0':(100,25),
    '4':(320,25),
    '5':(430,25),
    '6':(540,25),
    '8':(650,25),
    '9':(760,25),
    '10':(870,25),
}

all_rolls = list(range(2,13))
BETS = {

    #name: Bet(highlighter_size, highlighter_topleft, display_name, payoff, extra highlighter points, extra pos, extra size)

    'come'          :Bet((652,120),(178,252), 'Come',           {'1/1':all_rolls}),
    'field'         :Bet((542,117),(288,373), 'Field',          {'1/1':[3,4,9,10,11], '2/1':[2,12]}, 
                        [[(0,0), (109,0), (109,121)]], (180,372), (110,120)),
    'dont_pass'     :Bet((542,65),(288,493), 'Dont\'t Pass',    {'1/1':all_rolls}),
    'pass'          :Bet((662,65),(170,570), 'Pass',            {'1/1':all_rolls}),
    'dont_pass_odds':Bet((331,65),(502,645), 'Dont\'t Pass Odds',{'2/1':all_rolls}),
    'pass_odds'     :Bet((331,65),(170,645), 'Pass Odds',       {'2/1':all_rolls}),
    'dont_come'     :Bet((100,190),(180,53), 'Dont\'t Come',    {'1/1':all_rolls}),
    'any_seven'     :Bet((388,45),(964,295), 'Any Seven',       {'5/1':all_rolls}),
    'hard_6'        :Bet((194,80),(964,342), 'Hard Six',          {'10/1':all_rolls}),
    'hard_10'       :Bet((194,80),(1161,342), 'Hard Ten',        {'8/1':all_rolls}),
    'hard_4'        :Bet((194,80),(1161,431), 'Hard Four',         {'8/1':all_rolls}),
    'hard_8'        :Bet((194,80),(965,431), 'Hard Eight',          {'10/1':all_rolls}),
    '11_craps'      :Bet((194,80),(965,603), 'Horn 11 Craps',        {'16/1':all_rolls}),
    '3_craps'       :Bet((194,80),(1161,603), 'Horn 3 Craps',      {'16/1':all_rolls}),
    '2_craps'       :Bet((194,80),(965,517), 'Horn 2 Craps',            {'31/1':all_rolls}),
    '12_craps'      :Bet((194,80),(1161,517), 'Horn 12 Craps',      {'31/1':all_rolls}),
    'any_craps'     :Bet((388,45),(964,689), 'Any Craps',       {'8/1':all_rolls}),
    'big 6'         :Bet((67,125),(113,371), 'Big 6',           {'1/1':all_rolls},
                        [[(67,0), (117,60), (65,121)], [(0,124),(65,121),(16,175)]], (113,371), (120,200)),
    'big 8'         :Bet((105,67),(179,497), 'Big 8',           {'1/1':all_rolls},
                        [[(120,10), (178,76), (60,77)], [(18,124),(65,77),(66,145)]], (113,420), (200,150)),
    'place_lose_4'  :Bet((106,15),(288,53), 'Place Against 4',     {'5/11':all_rolls}),
    'lay_4'         :Bet((106,15),(288,75), 'Lay 4',            {'1/1':all_rolls}),
    'buy_4'         :Bet((106,15),(288,206), 'Buy 4',           {'1/1':all_rolls}),
    'place_win_4'   :Bet((106,15),(288,229), 'Place 4 to Win',     {'9/5':all_rolls}),
    'place_lose_5'  :Bet((106,15),(396,53), 'Place Against 5',     {'4/6':all_rolls}),
    'lay_5'         :Bet((106,15),(396,75), 'Lay 5',            {'1/1':all_rolls}),
    'buy_5'         :Bet((106,15),(396,206), 'Buy 5',           {'1/1':all_rolls}),
    'place_win_5'   :Bet((106,15),(396,229), 'Place 5 to Win',     {'7/6':all_rolls}),
    'place_lose_6'  :Bet((106,15),(506,53), 'Place Against 6',     {'4/6':all_rolls}),
    'lay_6'         :Bet((106,15),(506,75), 'Lay 6',            {'1/1':all_rolls}),
    'buy_6'         :Bet((106,15),(506,206), 'Buy 6',           {'1/1':all_rolls}),
    'place_win_6'   :Bet((106,15),(506,229), 'Place 6 to Win',     {'7/6':all_rolls}),
    'place_lose_8'  :Bet((106,15),(615,53), 'Place Against 8',     {'4/6':all_rolls}),
    'lay_8'         :Bet((106,15),(615,75), 'Lay 8',            {'1/1':all_rolls}),
    'buy_8'         :Bet((106,15),(615,206), 'Buy 8',           {'1/1':all_rolls}),
    'place_win_8'   :Bet((106,15),(615,229), 'Place 8 to Win',     {'7/6':all_rolls}),
    'place_lose_9'  :Bet((106,15),(725,53), 'Place Against 9',     {'5/8':all_rolls}),
    'lay_9'         :Bet((106,15),(725,75), 'Lay 9',            {'1/1':all_rolls}),
    'buy_9'         :Bet((106,15),(725,206), 'Buy 9',           {'1/1':all_rolls}),
    'place_win_9'   :Bet((106,15),(725,229), 'Place 9 to Win',     {'7/5':all_rolls}),
    'place_lose_10' :Bet((106,15),(834,53), 'Place Against 10',    {'5/11':all_rolls}),
    'lay_10'        :Bet((106,15),(834,75), 'Lay 10',           {'1/1':all_rolls}),
    'buy_10'        :Bet((106,15),(834,206), 'Buy 10',          {'1/1':all_rolls}),
    'place_win_10'  :Bet((106,15),(834,229), 'Place 10 to Win',    {'9/5':all_rolls}),

    'CE_eleven'     :Bet((30,30),(876,390), 'Yo Eleven',       {'7/1':all_rolls}),
    'CE_craps'     :Bet((30,30),(920,401), 'Any Craps',       {'7/1':all_rolls}),
}