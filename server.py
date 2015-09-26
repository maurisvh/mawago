#!/usr/bin/python
import uuid

from flask import Flask, redirect, render_template, request, \
    send_from_directory, url_for
from flask_socketio import SocketIO
from mawago import Mawago

app = Flask(__name__, static_folder='static')
app.debug = True
PORT = 8080
socketio = SocketIO(app)

waiting = {}
waiting_namespace = {}
games = {}


def new_id():
    return uuid.uuid4().hex


@app.route('/<path:path>')
def serve_file(path):
    return send_from_directory(app.static_folder, path)


@app.route('/')
def route_home():
    return render_template('home.html')


@app.route('/create', methods=['POST'])
def route_create():
    game_id = new_id()
    player_id = new_id()
    waiting[game_id] = (player_id, request.form['play_as'])
    return redirect(url_for('route_waiting', game_id=game_id))


@app.route('/waiting/<game_id>')
def route_waiting(game_id):
    return render_template('waiting.html', game_id=game_id)


@socketio.on('waiting')
def handle_waiting(json):
    game_id = json['game_id']
    if game_id in waiting:
        waiting_namespace[game_id] = request.namespace
    else:
        print 'Invalid waiting request?', game_id


@app.route('/join/<game_id>')
def route_join(game_id):
    try:
        print waiting
        host_id, play_as = waiting[game_id]
        del waiting[game_id]
    except KeyError:
        return 'No such game: ' + game_id

    try:
        host_ns = waiting_namespace[game_id]
        del waiting_namespace[game_id]
    except KeyError:
        return 'Sorry, this game is closed.'

    join_id = new_id()
    p1, p2 = (host_id, join_id) if play_as == '1' else (join_id, host_id)
    games[game_id] = Mawago(p1, p2)

    # The host plays as host_id...
    host_ns.emit('joined', {'game_id': game_id, 'player_id': host_id})

    # And the player who joined plays as join_id.
    url = url_for('route_game', game_id=game_id, player_id=join_id)
    return redirect(url)


@app.route('/game/<game_id>/<player_id>')
def route_game(game_id, player_id):
    return render_template('game.html',
                           game_id=game_id,
                           player_id=player_id)


@socketio.on('playing')
def handle_playing(json):
    print 'handle_playing', json
    try:
        game_id = json['game_id']
        game = games[game_id]
        player_id = json['player_id']
    except KeyError:
        return

    if player_id in (game.p1, game.p2):
        request.namespace.emit('verified')
        game.namespaces[player_id] = request.namespace
        game.update()


@socketio.on('move')
def handle_move(json):
    print 'handle_move', json
    try:
        game_id = json['game_id']
        game = games[game_id]
        player_id = json['player_id']
        x = json['x']
        y = json['y']
        quadrant = json['quadrant']
        direction = json['direction']
        game.move(player_id, (x, y), quadrant, direction)
        game.update()
    except KeyError, e:
        print 'err'
        print e
        return


print 'Starting a Mawago server on port {}.'.format(PORT)
socketio.run(app, port=PORT)
