def grid(n):
    for y in xrange(n):
        for x in xrange(n):
            yield (x, y)


class Mawago(object):
    def __init__(self, p1, p2):
        """Create a new game between the given player IDs."""
        self.p1 = p1
        self.p2 = p2
        self.current = p1
        self.board = {k: None for k in grid(6)}
        self.namespaces = {}
        self.moves = 0

    def json_state(self, player):
        """Return a JSON-compatible representation of the board.

        `player` is the player it will get sent to: the `can_play` field
        depends on this."""
        entry = {self.p1: '1', self.p2: '2', None: None}
        return (
            {'board': {x: {y: entry[self.board[x, y]]
                           for y in range(6)}
                       for x in range(6)},
             'can_play': (player == self.current
                          and self.win() is None
                          and not self.is_draw())}
        )

    def move(self, p, pos, quadrant, direction):
        """Make a move, then swap current player and opponent."""
        if (self.current == p
                and self.board.get(pos, '') is None
                and quadrant in ('tl', 'tr', 'bl', 'br')
                and direction in ('cw', 'ccw')
                and self.win() is None):
            self.board[pos] = self.current
            self.turn(quadrant, direction)
            self.current = self.opponent()
            self.moves += 1
        else:
            print 'Invalid move request?'
            print pos, quadrant, direction

    def opponent(self):
        """Get the player who isn't currently making a move."""
        return self.p1 if self.current == self.p2 else self.p2

    def turn(self, quadrant, direction):
        dx, dy = {'tl': (0, 0), 'tr': (3, 0),
                  'bl': (0, 3), 'br': (3, 3)}[quadrant]
        turn = {(x+dx, y+dy): (y+dx, 2-x+dy) for x, y in grid(3)}
        times = {'cw': 1, 'ccw': 3}[direction]
        for _ in range(times):
            self.board = {k: self.board[turn.get(k, k)] for k in self.board}

    wins = []
    for sx, sy in grid(6):
        for dx, dy in [(1, 0), (0, 1), (1, 1), (-1, 1)]:
            win = [(sx + k * dx, sy + k * dy) for k in range(5)]
            if all(0 <= x < 6 and 0 <= y < 6 for (x, y) in win):
                wins.append(win)

    def win(self):
        for win in self.wins:
            s = set(self.board[k] for k in win)
            for p in (self.p1, self.p2):
                if s == {p}:
                    return p
        return None

    def is_draw(self):
        return self.moves >= 6 * 6

    def update(self):
        for p, n in self.namespaces.items():
            n.emit('update', self.json_state(p))
