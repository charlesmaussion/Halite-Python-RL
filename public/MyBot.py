import sys
import os

module_path = os.path.abspath(os.path.join('..'))
if module_path not in sys.path:
    sys.path.append(module_path)

mode = 'server' if (len(sys.argv) == 1) else 'local'
mode = 'local'  # TODO remove forcing

if mode == 'server':  # 'server' mode
    import hlt
else:  # 'local' mode
    from networking.hlt_networking import HLT

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    hlt = HLT(port=port)

from public.models.bot.trainedBot import TrainedBot

bot = TrainedBot()

while True:
    myID, game_map = hlt.get_init()
    bot.setID(myID)
    hlt.send_init("MyBot")

    while (mode == 'server' or hlt.get_string() == 'Get map and play!'):
        game_map.get_frame(hlt.get_string())
        moves = bot.compute_moves(game_map)
        hlt.send_frame(moves)
