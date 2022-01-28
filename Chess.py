import pygame, os, time
from math import fabs
import pickle as pk

pygame.init()

windowinfo = pygame.display.Info()
gamewidth, gameheight = windowinfo.current_w, windowinfo.current_h
screen, clock = pygame.display.set_mode((gamewidth, gameheight), pygame.FULLSCREEN), pygame.time.Clock()
pygame.display.set_caption("Chess")

pygame.display.set_icon(pygame.image.load(os.path.join("pieces", "bPawn.png")))
boardRect = (int(135/1920*gamewidth), int(135/1080*gameheight), int(760/1920*gamewidth), int(760/1080*gameheight))
oppSide = {"w": "b", "b": "w", None: None}
checkHere = {"Knight": [[2, 1], [1, 2], [-1, 2], [-2, 1], [-2, -1], [-1, -2], [1, -2], [2, -1]],
             "Bishop": [[1, 1], [2, 2], [3, 3], [4, 4], [5, 5], [6, 6], [7, 7]],
             "Castle": [[[1, 0], [2, 0], [3, 0], [4, 0], [5, 0], [6, 0], [7, 0]], [[0, 1], [0, 2], [0, 3], [0, 4], [0, 5], [0, 6], [0, 7]]],
             "King": [[0, 1], [1, 1], [1, 0], [1, -1], [0, -1], [-1, -1], [-1, 0], [-1, 1]]}
kingMoved = [False, False]

font = "comicsansms"


def getLayout(num):
    if num == 0:
        return [["bCastle", "bKnight", "bBishop", "bQueen", "bKing", "bBishop", "bKnight", "bCastle"],
                ["bPawn", "bPawn", "bPawn", "bPawn", "bPawn", "bPawn", "bPawn", "bPawn"],
                [None, None, None, None, None, None, None, None],
                [None, None, None, None, None, None, None, None],
                [None, None, None, None, None, None, None, None],
                [None, None, None, None, None, None, None, None],
                ["wPawn", "wPawn", "wPawn", "wPawn", "wPawn", "wPawn", "wPawn", "wPawn"],
                ["wCastle", "wKnight", "wBishop", "wQueen", "wKing", "wBishop", "wKnight", "wCastle"]]
    elif num == 1:
        return [["bKing", None, None, None, None, None, None, None],
               [None, None, None, None, None, None, None, "wQueen"],
               [None, None, None, None, None, None, "wQueen", None],
               [None, None, None, None, None, None, None, None, None],
               [None, None, None, None, None, None, None, None, None],
               [None, None, None, None, None, None, None, None, None],
               [None, None, None, None, None, None, None, None, None],
               [None, None, None, None, "wKing", None, None, None, None]]
    elif num == 2:
        return [["bKing", None, None, None, None, None, None, None],
                [None, None, None, None, None, None, None, None],
                [None, None, None, None, None, None, None, None],
                [None, None, None, None, None, None, None, None],
                [None, None, None, None, None, None, None, None],
                [None, None, None, None, "wKing", None, None, None],
                [None, None, None, None, None, None, None, None],
                [None, None, None, None, None, None, None, None]]


startLayout = getLayout(0)


class Info:
    fullInfo = {"w": "White", "b": "Black"}
    nameToPoints = {"Pawn": 1, "Knight": 3, "Bishop": 3, "Castle": 5, "Queen": 9, "King": 404}

    def __init__(self):
        self.saveButton = Button([1045/1920*gamewidth, 775/1080*gameheight, 415/1920*gamewidth, 50/1080*gameheight], "Save Game")
        self.backButton = Button([1045/1920*gamewidth, 835/1080*gameheight, 200/1920*gamewidth, 50/1080*gameheight], "<---")
        self.menuButton = Button([1260/1920*gamewidth, 835/1080*gameheight, 200/1920*gamewidth, 50/1080*gameheight], "Menu")

    def reset(self, stuff, array):
        time1, time2 = stuff["time1"], stuff["time2"]
        self.autoQueen = stuff["autoQueen"]
        self.allowBack = stuff["allowBack"]
        if stuff["array"] is not None:
            array = wordToArray(stuff["array"])
        self.name1, self.name2 = stuff["name1"], stuff["name2"]
        enPassent = stuff["enPassent"]
        if enPassent:
            self.allowEnPassent = True
            for row, erow in zip(array, enPassent):
                for piece, allow in zip(row, erow):
                    piece.enPassent = allow
        else:
            self.allowEnPassent = False

        self.times, self.side = [time1, time2], "w"
        self.countdown = False
        self.seconds = [time.time(), time.time()]
        self.taken, self.moves, self.orderTaken = [[], []], [], []
        self.kingsMoves = []
        self.CHECK, self.MATE, self.STALE, self.DRAW = [False, False], [False, False], [False, False], False
        self.prevArrays, self.prevTimes = [], []
        self.endGame(array)
        return array

    def active(self, array):
        self.render()
        return self.buttons(array)

    def buttons(self, array):
        self.goToMenu()
        self.save(array)
        if self.allowBack:
            array = self.back(array)
        return array

    def save(self, array):
        if self.saveButton.active():
            if not os.path.exists("saves"):
                os.mkdir("saves")

            if self.allowEnPassent:
                enpassent = [[piece.enPassent for piece in row] for row in array]
            else:
                enpassent = False

            save = {"array": [[piece.name for piece in row] for row in array], "moves": self.moves, "taken": self.taken,
                    "time": self.times, "side": self.side, "orderTaken": self.orderTaken, "prevArrays": self.prevArrays,
                    "prevTimes": self.prevTimes, "kingsMoves": self.kingsMoves, "name1": self.name1, "name2": self.name2,
                    "enPassent": enpassent}

            filename = saveGUI("saves")

            with open("save/{}.pkl".format(filename), "wb") as file:
                pk.dump(save, file, pk.HIGHEST_PROTOCOL)

    def load(self, array, save):
        for j, row in enumerate(array):
            for i, piece in enumerate(row):
                piece.change(save["array"][j][i])

        self.moves = save["moves"]
        self.taken = save["taken"]
        self.times = save["time"]
        self.side = save["side"]
        self.orderTaken = save["orderTaken"]
        self.prevArrays = save["prevArrays"]
        self.prevTimes = save["prevTimes"]
        self.kingsMoves = save["kingsMoves"]
        self.name1 = save["name1"]
        self.name2 = save["name2"]
        self.allowEnPassent = save["enPassent"]
        return array

    def goToMenu(self):
        if self.menuButton.active():
            rect = [gamewidth/2 - 150/1920*gamewidth, gameheight/2 - 50/1080*gameheight, 300/1920*gamewidth, 100/1080*gamewidth]
            yes = Button([rect[0], rect[1] + rect[3]/2, rect[2]/2, rect[3]/2], "Yes")
            no = Button([rect[0] + rect[2]/2, rect[1] + rect[3]/2, rect[2]/2, rect[3]/2], "No")
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        quit()

                screen.fill([75, 75, 75], rect)
                text(screen, [5, 5, 5], [rect[0] + rect[2]/2, rect[1] + rect[3]/4], int(rect[3]/6), "Return to Menu?", font, True)

                if yes.active():
                    menu()
                    pygame.quit()
                    quit()

                if no.active():
                    break

                pygame.draw.rect(screen, [35, 35, 35], rect, 5)
                pygame.draw.line(screen, [35, 35, 35], [rect[0], rect[1] + rect[3]/2], [rect[0] + rect[2], rect[1] + rect[3]/2], 5)
                pygame.draw.line(screen, [35, 35, 35], [rect[0] + rect[2]/2, rect[1] + rect[3]/2], [rect[0] + rect[2]/2, rect[1] + rect[3]], 5)

                pygame.display.update(rect)

    def back(self, array):
        if self.backButton.active() and len(self.prevArrays) > 0:
            oldarray = self.prevArrays.pop(-1)
            self.times = self.prevTimes.pop(-1)  # [:]
            self.moves.pop(-1)
            if self.orderTaken[-1] is not None:
                val = {"w": 0, "b": 1}[self.orderTaken[-1][0]]
                self.taken[val].remove(self.orderTaken[-1])
            self.orderTaken.pop(-1)
            self.kingsMoves.pop(-1)
            try:
                kingMoved[0] = self.kingsMoves[-1][0]
                kingMoved[1] = self.kingsMoves[-1][1]
            except:
                pass
            self.switch()
            self.CHECK, self.CHEAT = self.check(array)

            newarray = []
            for j, row in enumerate(oldarray):
                newarray.append([])
                for i, piece in enumerate(row):
                    newarray[-1].append(Piece(piece, i, j, boardRect[2]/8, boardRect[3]/8))

            array = newarray[:]

        return array

    def backup(self, oldarray):
        ting = []
        for row in oldarray:
            ting.append([])
            for piece in row:
                ting[-1].append(piece.name)
        self.prevArrays.append(ting)

    def addtoMoves(self, castle, args):
        if castle:
            if args == "Queen": self.moves.append("O-O-O")
            else: self.moves.append("O-O")
        else:
            fromCell = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'][args[0]] + ['8', '7', '6', '5', '4', '3', '2', '1'][args[1]]
            toCell = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'][args[2]] + ['8', '7', '6', '5', '4', '3', '2', '1'][args[3]]
            self.moves.append("{}-{}".format(fromCell, toCell))

    def check(self, testarray):
        inCheck = [True, True]
        count = [0, 0]
        wPlaces, bPlaces = [], []
        wking, bking = None, None
        for j, row in enumerate(testarray):
            for i, piece in enumerate(row):
                if piece.used:
                    count[{"w": 0, "b": 1}[piece.side]] += 1
                    places = getRawPlaces(piece.name, piece.side, i, j, testarray)
                    if piece.side == "w":
                        for pla in places:
                            if pla not in wPlaces:
                                wPlaces.append(pla)
                    else:
                        for pla in places:
                            if pla not in bPlaces:
                                bPlaces.append(pla)

                if piece.name == "bKing":
                    bking = [i, j]
                elif piece.name == "wKing":
                    wking = [i, j]

        if wking not in bPlaces:
            inCheck[0] = False

        if bking not in wPlaces:
            inCheck[1] = False

        return inCheck, [not count[0], not count[1]]

    def endGame(self, array):
        self.CHECK, self.CHEAT = self.check(array)
        mate, draw = checkMATE(array)
        if True in self.CHECK:
            self.MATE = mate
        else:
            self.STALE, self.DRAW = mate, draw

    def render(self):
        texts = [self.name1, self.name2]
        for i in range(2):
            if self.MATE[i]:
                texts[i] += " - Checkmate"
            elif self.CHECK[i]:
                texts[i] += " - Check"
        text(screen, (0, 0, 0), [boardRect[0], 15/1080*gameheight], int(boardRect[2]/16), texts[1], font, False)
        text(screen, (255, 255, 255), [boardRect[0], 930/1080*gameheight], int(boardRect[2]/16), texts[0], font, False)
        text(screen, (0, 0, 0) if self.side == "b" else (235, 235, 235), [1025/1920*gamewidth, 135/1080*gameheight], int(gameheight / 15), "{}'s turn".format(self.fullInfo[self.side]), font, False)

        self.renderTakenPieces()
        self.renderMoveInfo()
        self.renderTimes()

    def renderTimes(self):
        self.seconds[1] = time.time()
        rects = [[610/1920*gamewidth, 70/1080*gameheight, 280/1920*gamewidth, 50/1080*gameheight], [610/1920*gamewidth, 910/1080*gameheight, 280/1920*gamewidth, 50/1080*gameheight]]
        for i, rect in enumerate(rects):
            pygame.draw.rect(screen, (75, 75, 75), rect)
            pygame.draw.rect(screen, (25, 25, 25), rect, 2)
            col = [5, 5, 5] if self.times[i] > 10 else [235, 0, 0]
            if self.times[i] < 0: showTime = 0
            else: showTime = self.times[i]
            text(screen, col, getMidRect(rect), int(rect[3]*(2/3)), self.getCoolTime(showTime), font, True)

            if i == {"b": 0, "w": 1}[self.side]:
                if self.seconds[0] < self.seconds[1] and self.countdown:
                    multi = 1
                    if self.times[i] < 10:
                        multi = 0.1

                    self.seconds[0] = time.time() + multi
                    self.times[i] -= multi

    def renderTakenPieces(self):
        y = boardRect[1] - 30/1080*gameheight
        points, xs, ys = [0, 0], [0, 0], [y, 0]
        for k, sid in enumerate(self.taken):
            sid = sorted(sid)
            x = boardRect[0]
            for i, piece in enumerate(sid):
                screen.blit(pygame.transform.scale(loadImage(piece, "pieces"), [int(25/1920*gamewidth), int(25/1080*gameheight)]), [x, y])
                if len(sid) - 1 != i:
                    if piece == sid[i + 1]:
                        x += 15/1920*gamewidth
                    else:
                        x += 40/1920*gamewidth

                points[k] += self.nameToPoints[piece[1:]]

            y = boardRect[1] + boardRect[3] + 5
            ys[1], xs[k] = y, x

        if points[0] > points[1]:
            bigger = points[0] - points[1]
            text(screen, [100, 100, 100], [xs[0] + 50/1080*gameheight, ys[0] - 5], int(25/1080*gameheight), "+" + str(bigger), font, False)
        elif points[1] > points[0]:
            bigger = points[1] - points[0]
            text(screen, [100, 100, 100], [xs[1] + 50/1080*gameheight, ys[1] - 5], int(25/1080*gameheight), "+" + str(bigger), font, False)

    def renderMoveInfo(self):
        moveRect = [1040 / 1920 * gamewidth, 235 / 1080 * gameheight, 425 / 1920 * gamewidth, 525 / 1080 * gameheight]
        screen.fill((75, 75, 75), moveRect)
        pygame.draw.rect(screen, [35, 35, 35], moveRect, 5)
        pygame.draw.line(screen, [35, 35, 35], [moveRect[0] + moveRect[2]/2, moveRect[1]], [moveRect[0] + moveRect[2]/2, moveRect[1] + moveRect[3]], 5)
        pygame.draw.line(screen, [35, 35, 35], [moveRect[0], moveRect[1] + moveRect[3]/15], [moveRect[0] + moveRect[2], moveRect[1] + moveRect[3]/15], 5)
        text(screen, [215, 215, 215], [int(moveRect[0] + 3), int(moveRect[1] - 7)], int(moveRect[3]/15), "White", font, False)
        text(screen, [25, 25, 25], [int(moveRect[0] + 3 + moveRect[2]/2), int(moveRect[1] - 7)], int(moveRect[3]/15), "Black", font, False)
        y = moveRect[1] + moveRect[3]/15
        for i, move in enumerate(self.moves):
            if len(self.moves) > 47:
                if i > len(self.moves) - 47:
                    y = self.renderTheTing(i, y, moveRect, move)
            else:
                y = self.renderTheTing(i, y, moveRect, move)

    def renderTheTing(self, i, y, moveRect, move):
        if (i + 1) % 2 == 0:
            text(screen, [25, 25, 25], [moveRect[0] + moveRect[2]/2 + 5, y], int(17/1080*gameheight), move, font, False)
            y += 20/1080*gameheight
        else:
            text(screen, [215, 215, 215], [moveRect[0] + 5, y], int(17/1080*gameheight), "{}: {}".format(int((i+1)/2)+1, move), font, False)
        return y

    def switch(self):
        self.side = oppSide[self.side]

    def take(self, name):
        if name[0] == "w":
            self.taken[0].append(name)
        else:
            self.taken[1].append(name)

    def getCoolTime(self, getTime):
        theTime = int(getTime)
        hours = int(theTime / 3600)
        minutes = int(theTime / 60)

        minute = minutes - hours * 60
        if getTime < 10 and int(getTime) != getTime:
            second = float(str(getTime)[:3]) - minutes * 60 - hours * 3600
        else:
            second = theTime - minute * 60 - hours * 3600

        timeStr = ""
        if hours > 0:
            timeStr += str(hours) + "h  "
        if minute > 0:
            timeStr += str(minute) + "m  "
        timeStr += str(second) + "s"
        return timeStr


class Piece:
    def __init__(self, name, i, j, w, h, brect = boardRect):
        self.i, self.j, self.w, self.h = i, j, w, h
        self.boardRect = brect
        self.change(name)

    def active(self):
        self.render()

    def change(self, name):
        if name is not None:
            self.name, self.side = name, name[0]
            self.image = pygame.transform.scale(loadImage(name, "pieces"), [int(self.w-20), int(self.h-20)])
            self.used, self.show = True, True
            self.imageRect = self.image.get_rect()
            self.imageRect.center = [self.boardRect[0] + self.i*self.w + self.w/2, self.boardRect[1] + self.j*self.h + self.h/2]
            self.rect = [self.boardRect[0] + self.i*self.w, self.boardRect[1] + self.j*self.h, self.w, self.h]

        else:
            self.name, self.side = None, None
            self.image = None
            self.imageRect, self.rect = None, None
            self.used, self.show = False, False
        self.enPassent = False

    def render(self):
        if self.used and self.show:
            screen.blit(self.image, self.imageRect)

    def clicked(self, mousepos):
        if self.used:
            if pointInRect(mousepos, self.rect):
                return True, self.name

        return False, None


class MovingPiece:
    def __init__(self, name, i, j, array):
        self.name, self.side = name, name[0]
        self.i, self.j = i, j
        self.w, self.h = boardRect[2]/8, boardRect[3]/8
        self.image = pygame.transform.scale(loadImage(name, "pieces"), [int(self.w-20), int(self.h-20)])
        self.imageRect = self.image.get_rect()
        self.places = getGoodPlaces(self.name, self.side, self.i, self.j, array)

    def active(self, array):
        array, delete = self.place(array)
        self.render()
        return array, delete

    def render(self):
        for pla in self.places:
            x, y = boardRect[0] + pla[0]*self.w, boardRect[1] + pla[1]*self.h
            pygame.draw.circle(screen, (0, 200, 0), [int(x + self.w/2), int(y + self.h/2)], int(self.w/8))
        mousepos, mousepress = getmouse()
        self.imageRect.center = mousepos
        screen.blit(self.image, self.imageRect)

    def place(self, array):
        mousepos, mousepress = getmouse()
        if not mousepress[0]:
            i, j = int((mousepos[0] - boardRect[0])/self.w), int((mousepos[1] - boardRect[1])/self.h)
            if canGoHere(self.name, self.side, self.i, self.j, i, j, array):
                info.backup(array)
                info.kingsMoves.append(kingMoved)
                castle, args = False, [self.i, self.j, i, j]
                if array[j][i].side == oppSide[self.side]:
                    info.take(array[j][i].name)

                info.orderTaken.append(array[j][i].name)
                info.prevTimes.append(info.times[:])

                empty = False if array[j][i].used else True
                array[j][i].change(self.name)
                info.countdown = True
                if info.allowEnPassent:
                    for row in array:
                        for piece in row:
                            piece.enPassent = False

                if self.name[1:] == "Pawn":
                    if info.allowEnPassent:
                        if fabs(j - self.j) == 2:
                            array[j][i].enPassent = True
                        multi = {"w": -1, "b": 1}[self.side]
                        if empty:
                            if [self.i - 1, self.j + multi] == [i, j]:
                                info.take(array[self.j][i].name)
                                array[self.j][i].change(None)
                                info.orderTaken[-1] = oppSide[self.side] + "Pawn"
                            elif [self.i + 1, self.j + multi] == [i, j]:
                                info.take(array[self.j][i].name)
                                array[self.j][i].change(None)
                                info.orderTaken[-1] = oppSide[self.side] + "Pawn"

                elif self.name[1:] == "King":
                    if self.i - i == 2:
                        castle = True
                        array[j][i+1].change(self.side + "Castle")
                        try:
                            for k in range(1, 3, 1):
                                if k == 2: args = "Queen"
                                else: args = "King"
                                if array[j][i-k].name == self.side + "Castle":
                                    array[j][i-k].change(None)
                                    break
                        except:
                            pass

                    elif i - self.i == 2:
                        castle, args = True, "Queen"
                        array[j][i - 1].change(self.side + "Castle")
                        try:
                            for k in range(1, 3, 1):
                                if k == 2: args = "Queen"
                                else: args = "King"
                                if array[j][i+k].name == self.side + "Castle":
                                    array[j][i+k].change(None)
                                    break
                        except:
                            pass

                info.addtoMoves(castle, args)
                if self.name == "wKing": kingMoved[1] = True
                elif self.name == "bKing": kingMoved[0] = True
                array[self.j][self.i].change(None)
                array = switchPawn(array)
                info.switch()
                info.endGame(array)

            else:
                array[self.j][self.i].show = True
        else:
            return array, False

        return array, True


class Button:
    def __init__(self, rect, words):
        self.rect, self.words = rect, words
        self.clicked = False
        self.col1, self.col2 = (75, 75, 75), [35, 35, 35]

    def active(self):
        mousepos, mousepress = getmouse()
        if pointInRect(mousepos, self.rect):
            self.render(self.col2)
            if mousepress[0] and not self.clicked:
                self.clicked = True
            if not mousepress[0] and self.clicked:
                self.clicked = False
                return True
        else:
            self.render(self.col1)

    def render(self, col):
        screen.fill(col, self.rect)
        size = int(self.rect[3]/2)
        while True:
            test = pygame.font.SysFont(font, size)
            width, height = test.size(self.words)
            if width > self.rect[2]:
                size -= 1
            else:
                break

        text(screen, [15, 15, 15], [int(self.rect[0] + self.rect[2]/2), int(self.rect[1] + self.rect[3]/2)], size, self.words, font, True)


class BooleanButton(Button):
    def __init__(self, rect, start=False):
        self.rect, self.clicked, self.current = rect, False, start
        self.col1, self.col2 = (75, 75, 75), [35, 35, 35]

    def activate(self):
        state = self.active()
        if state:
            self.current = not self.current

    def render(self, col):
        screen.fill(col, self.rect)
        pygame.draw.rect(screen, [15, 15, 15], self.rect, 3)
        if self.current:
            screen.fill([15, 15, 15], [self.rect[0]+self.rect[2]/8, self.rect[1]+self.rect[3]/8, self.rect[2]-self.rect[2]/4, self.rect[3]-self.rect[3]/4])


class CustomBoard_PiecePlacement:
    def __init__(self):
        self.change(None)

    def change(self, piece):
        self.piece = piece
        if piece is None:
            self.name, self.side = None, None
        else:
            self.name, self.side = piece[1:], piece[0]


class numBox:
    def __init__(self, rect, minimum, maximum, start):
        self.rect, self.min, self.max = rect, minimum, maximum
        self.number = start

    def active(self, background):
        hover = self.add(background)
        self.inRange()
        self.render(hover)

    def add(self, background):
        mousepos, mousepress = getmouse()
        if pointInRect(mousepos, self.rect):
            if mousepress[0]:
                while True:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            quit()

                        if event.type == pygame.KEYDOWN:
                            if event.unicode in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]:
                                test = pygame.font.SysFont(font, int(self.rect[3]/2))
                                width, height = test.size(str(self.number) + event.unicode)
                                if width < self.rect[2]:
                                    self.number = int(str(self.number) + event.unicode)
                            elif event.key == 8:
                                try:
                                    self.number = int(str(self.number)[:-1])
                                except: self.number = 0

                        if event.type == pygame.MOUSEBUTTONDOWN:
                            if not pointInRect(event.pos, self.rect):
                                return False

                    screen.blit(background, [0, 0])

                    self.render(True)

                    pygame.display.update()
            else:
                return True
        return False

    def inRange(self):
        if self.number < self.min:
            self.number = self.min

        if self.number > self.max:
            self.number = self.max

    def render(self, hover):
        screen.fill((70, 70, 70), self.rect)
        if hover:
            col = [45, 45, 45]
        else:
            col = [25, 25, 25]
        pygame.draw.rect(screen, col, self.rect, 4)

        text(screen, col, getMidRect(self.rect), int(self.rect[3]/2), str(self.number), font, True)


class TextBox:
    badChars = '\\/:*?"<>|'

    def __init__(self, rect):
        self.rect = rect
        self.text = ""

    def active(self):
        hover = self.input()
        self.render(hover)

    def input(self):
        hover = False
        mousepos, mousepress = getmouse()
        if pointInRect(mousepos, self.rect):
            hover = True
            if mousepress[0]:
                screenCopy = screen.copy()
                while True:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            quit()

                        if event.type == pygame.KEYDOWN:
                            key = event.unicode
                            if event.key == 8 and len(self.text) > 0:
                                self.text = self.text[:-1]
                            elif key not in self.badChars:
                                test = pygame.font.SysFont(font, int(self.rect[3] - self.rect[3]/10))
                                width, height = test.size(self.text + key)
                                if width < self.rect[2]:
                                    self.text += key

                        if event.type == pygame.MOUSEBUTTONDOWN:
                            if not pointInRect(event.pos, self.rect):
                                return False

                    screen.blit(screenCopy, [0, 0])
                    self.render(True)

                    pygame.display.update()

        return hover

    def render(self, hover):
        col = [100, 100, 100] if hover else [85, 85, 85]
        screen.fill(col, self.rect)
        pygame.draw.rect(screen, [15, 15, 15], self.rect, 5)
        text(screen, [35, 35, 35], [self.rect[0] + self.rect[3]/10, self.rect[1] - self.rect[3]/4], int(self.rect[3] - self.rect[3]/10), self.text, font, False)


class NameReview:
    def __init__(self, rect, start, cols):
        self.rect, self.text, self.start = rect, start, start
        self.size = int(self.rect[3] - self.rect[3]/10)
        self.col1, self.col2 = cols

    def render(self, col):
        text(screen, col, [self.rect[0], self.rect[1]], self.size, self.text, font, False)

    def active(self, other):
        mousepos, mousepress = getmouse()
        if pointInRect(mousepos, self.rect):
            if mousepress[0]:
                background = screen.copy()
                while True:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            quit()

                        if event.type == pygame.KEYDOWN:
                            if event.key == 8:
                                if len(self.text) > 0:
                                    self.text = self.text[:-1]
                            elif event.key == 13:
                                if len(self.text) == 0:
                                    self.text = self.start
                                return
                            else:
                                test = pygame.font.SysFont(font, self.size)
                                width, height = test.size(self.text + event.unicode)
                                if width < self.rect[2]:
                                    self.text += event.unicode

                        if event.type == pygame.MOUSEBUTTONDOWN:
                            if not pointInRect(event.pos, self.rect):
                                if len(self.text) == 0:
                                    self.text = self.start
                                return

                    screen.blit(background, [0, 0])
                    self.render(self.col2)
                    other.render(other.col1)

                    pygame.display.update()

            else:
                self.render(self.col2)
        else:
            self.render(self.col1)


def getGoodPlaces(name, side, i, j, array, doCheck=True):
    num = side == "b"
    if info.CHECK[num] and doCheck:
        places = []
        checkPlaces = getGoodPlaces(name, side, i, j, array, False)
        array[j][i].change(None)
        for ni, nj in checkPlaces:
            orig = array[nj][ni].name
            array[nj][ni].change(name)

            if not info.check(array)[0][num]:
                places.append([ni, nj])

            array[nj][ni].change(orig)
        array[j][i].change(name)
        array[j][i].show = False

    else:
        places = getRawPlaces(name, side, i, j, array)

        # Checking for illegal moves
        removelist = []
        array[j][i].change(None)
        for ni, nj in places:
            orig = array[nj][ni].name
            array[nj][ni].change(name)

            if info.check(array)[0][num]:
                removelist.append([ni, nj])

            array[nj][ni].change(orig)
        array[j][i].change(name)
        array[j][i].show = False

        for item in removelist:
            places.remove(item)

        if name[1:] == "King":
            for k in [1, -1]:
                if [i + k, j] not in places and [i + k*2, j] in places:
                    places.remove([i + k*2, j])

    return places


def getRawPlaces(name, side, i, j, array):
    name = name[1:]
    places = []
    if name == "Bishop" or name == "Knight" or name == "Castle" or name == "King":
        checkMove = checkHere[name]
        if side == "w" and name == "Bishop":
            for ting in checkMove:
                ting[1] *= -1

    if name == "Pawn":
        if side == "w": multi = -1; start = 6
        else: multi = 1; start = 1
        checkThese = [[0, multi*1], [0, multi*2], [-1, multi*1], [1, multi*1]]
        if 0 <= j + checkThese[0][1] <= 7:
            if not array[j + checkThese[0][1]][i].used:
                places.append([i + checkThese[0][0], j + checkThese[0][1]])
                if 0 <= j + checkThese[1][1] <= 7 and j == start:
                    if not array[j + checkThese[1][1]][i].used:
                        places.append([i + checkThese[1][0], j + checkThese[1][1]])
        for k in range(2):
            moves = checkThese[2+k]
            ni, nj = i + moves[0], j + moves[1]
            if onBoard(ni, nj):
                if side == oppSide[array[nj][ni].side]:
                    places.append([ni, nj])

        if info.allowEnPassent:
            for k in [-1, 1]:
                oi = i + k
                if onBoard(oi, j):
                    if array[j][oi].name == oppSide[side] + "Pawn":
                        if array[j][oi].enPassent:
                            k = {"w": -1, "b": 1}[side]
                            places.append([oi, j+k])

    if name == "Knight":
        for ting in checkMove:
            ni, nj = i + ting[0], j + ting[1]
            if onBoard(ni, nj):
                if array[nj][ni].side != side:
                    places.append([ni, nj])

    if name == "Bishop" or name == "Queen":
        if name == "Queen":
            checkMove = checkHere["Bishop"]
        for k in range(4):
            for x, y in checkMove:
                if k == 0:
                    ni, nj = i + x, j + y
                elif k == 1:
                    ni, nj = i + x, j - y
                elif k == 2:
                    ni, nj = i - x, j - y
                else:
                    ni, nj = i - x, j + y

                if onBoard(ni, nj):
                    if array[nj][ni].side == side:
                        break
                    elif array[nj][ni].side == oppSide[side]:
                        places.append([ni, nj])
                        break
                    else:
                        places.append([ni, nj])
                else:
                    break

    if name == "Castle" or name == "Queen":
        if name == "Queen":
            checkMove = checkHere["Castle"]
        for k in range(2):
            for m in range(2):
                for x, y in checkMove[k]:
                    if m == 0 and k == 0:
                        ni, nj = i + x, j
                    elif m == 1 and k == 0:
                        ni, nj = i - x, j
                    elif m == 0 and k == 1:
                        ni, nj = i, j + y
                    elif m == 1 and k == 1:
                        ni, nj = i, j - y

                    if onBoard(ni, nj):
                        if array[nj][ni].side == side:
                            break
                        elif array[nj][ni].side == oppSide[side]:
                            places.append([ni, nj])
                            break
                        else:
                            places.append([ni, nj])

    if name == "King":
        for ting in checkMove:
            ni, nj = i + ting[0], j + ting[1]
            if onBoard(ni, nj):
                if side != array[nj][ni].side:
                    places.append([ni, nj])

        # Castling
        allowCastle = getCastling(array)
        if side == "w":
            castles = allowCastle[:2]
        else:
            castles = allowCastle[2:]
        for k, cas in enumerate(castles):
            if cas:
                places.append([i + 2*(2*k - 1), j])

    return places


def canGoHere(name, side, oi, oj, ni, nj, array):
    if not (ni == oi and nj == oj) and 0 <= ni <= 7 and 0 <= nj <= 7:
        if array[nj][ni].side == oppSide[array[oj][oi].side] or not array[nj][ni].used:
            places = getGoodPlaces(name, side, oi, oj, array)
            if [ni, nj] in places:
                return True

    return False


def getCastling(array):
    check = info.CHECK
    allowCastle = [not check[0], not check[0], not check[1], not check[1]]
    wKingRow, bKingRow = [], []
    for j, row in enumerate(array):
        for piece in row:
            if piece.name == "wKing":
                wKingRow = [row, j]
            if piece.name == "bKing":
                bKingRow = [row, j]

    count = 0
    for side, ting in zip(["w", "b"], [wKingRow, bKingRow]):
        if ting:
            castles, index = [[], []], 0
            castlesIndex = [[], []]
            for k, piece in enumerate(ting[0]):
                if piece.name == side + "Castle":
                    castles[index].append(side + "Castle")
                    castlesIndex[index].append(k)
                elif piece.name == side + "King":
                    castles[index].append(side + "King")
                    castlesIndex[index].append(k)
                    index = 1
                    castles[index].append(side + "King")
                    castlesIndex[index].append(k)
                elif len(castles[index]) > 0 and (side + "King" not in castles[index] or side + "Castle" not in castles[index]):
                    castles[index].append(piece.name)
                    castlesIndex[index].append(k)

            good = [side + "Castle", side + "King"]
            for i, part in enumerate(castles):
                for piece in part:
                    if piece is not None and piece not in good:
                        allowCastle[count + i] = False
                        break
                if side + "Castle" not in part:
                    allowCastle[count + i] = False

                elif not (part.count(None) == 3 or part.count(None) == 2):
                    allowCastle[count + i] = False

                for move in info.moves:
                    if ijToWord(castlesIndex[i][0], ting[1]) in move:
                        allowCastle[count + i] = False
                    elif ijToWord(castlesIndex[i][-1], ting[1]) in move:
                        allowCastle[count + i] = False

            count += 2

    return allowCastle


def switchPawn(array):
    side, pieces = "", ["Knight", "Bishop", "Castle", "Queen"]
    for i in range(8):
        if array[0][i].name == "wPawn":
            cell = array[0][i]
            rect = [cell.rect[0] + cell.rect[2] + 5, cell.rect[1] + cell.rect[3] + 5, (cell.rect[2] + cell.rect[2]/10)*4, cell.rect[3] + cell.rect[3]/10]
            oj, oi, side = 0, i, "w"
            break

        elif array[7][i].name == "bPawn":
            cell = array[7][i]
            rect = [cell.rect[0] + cell.rect[2] + 5, cell.rect[1] - (cell.rect[3] + cell.rect[3] / 10) - 5, (cell.rect[2] + cell.rect[2] / 10) * 4, cell.rect[3] + cell.rect[3] / 10]
            oj, oi, side = 7, i, "b"
            break

    if side != "":
        if info.autoQueen:
            array[oj][oi].change(side + "Queen")
            info.moves[-1] += "   P -> Q"
            return array
        else:
            array[oj][oi].change(side + "Pawn")
            array[oj][oi].render()
            while True:
                screen.fill((75, 75, 75), rect)

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        quit()

                mousepos, mousepress = getmouse()
                if pointInRect(mousepos, rect):
                    for i in range(4):
                        if pointInRect(mousepos, [rect[0] + (rect[2]/4)*i, rect[1], rect[2]/4, rect[3]]):
                            screen.fill([100, 100, 100], [rect[0] + rect[2]/4*i, rect[1], rect[2] / 4, rect[3]])
                            if mousepress[0]:
                                array[oj][oi].change(side + pieces[i])
                                info.moves[-1] += "   P -> {}".format(pieces[i][0])
                                return array

                pygame.draw.rect(screen, [35, 35, 35], rect, 3)
                x = rect[0]
                for name in pieces:
                    image = pygame.transform.scale(loadImage(side + name, "pieces"), [int(rect[2]/4 - rect[2]/80), int(rect[3] - rect[3]/20)])
                    screen.blit(image, [x + rect[2]/160, rect[1] + rect[3]/40])
                    x += rect[2]/4

                pygame.display.update()
    else:
        return array


def checkMATE(array):
    mate, draw = [True, True], True
    for j, row in enumerate(array):
        for i, piece in enumerate(row):
            if piece.used:
                if piece.name[1:] != "King":
                    draw = False

                name, side = piece.name, piece.name[0]
                ting = side == "b"
                if mate[ting]:
                    checkPlaces = getGoodPlaces(name, side, i, j, array, False)
                    array[j][i].change(None)
                    for ni, nj in checkPlaces:
                        orig = array[nj][ni].name
                        array[nj][ni].change(name)

                        if not info.check(array)[0][ting]:
                            mate[ting] = False

                        array[nj][ni].change(orig)
                    array[j][i].change(name)

    return mate, draw


def ijToWord(i, j):
    p1 = ["a", "b", "c", "d", "e", "f", "g", "h"][i]
    p2 = ["8", "7", "6", "5", "4", "3", "2", "1"][j]
    return p1+p2


def text(surface, col, pos, size, text, font, center):
    largetext = pygame.font.SysFont(font, size)
    if center:
        textsurf = largetext.render(text, True, col)
        textrect = textsurf.get_rect()
        textrect.center = pos
        surface.blit(textsurf, textrect)
    else:
        textsurf = largetext.render(text, True, col)
        surface.blit(textsurf, pos)


def getMidRect(rect):
    return [rect[0] + rect[2]/2, rect[1] + rect[3]/2]


def onBoard(i, j):
    return 0 <= i <= 7 and 0 <= j <= 7


def pointInRect(point, rect):
    return rect[0] < point[0] < rect[0] + rect[2] and rect[1] < point[1] < rect[1] + rect[3]


def loadImage(name, file):
    return pygame.image.load(os.path.join(file, name + ".png"))


def getmouse():
    return pygame.mouse.get_pos(), pygame.mouse.get_pressed()


def wordToArray(array, theRect=boardRect):
    return [[Piece(array[j][i], i, j, theRect[2]/8, theRect[3]/8) for i in range(8)] for j in range(8)]


def arrayToWord(array):
    return [[piece.name for piece in row] for row in array]


def genBoardImage(wh):
    w, h = int(wh[0]/8), int(wh[1]/8)
    surf = pygame.Surface(wh)
    for j in range(8):
        for i in range(8):
            if (i+j) % 2 == 0:
                surf.fill((255, 206, 158), [i*w, j*h, w, h])
            else:
                surf.fill((209, 139, 71), [i*w, j*h, w, h])
    return surf



def menu():
    escButton = Button([6, 6, 50/1920*gamewidth, 50/1080*gameheight], "X")
    pvpButton = Button([gamewidth/2 - gamewidth/4, gameheight/8 + 150/1080*gameheight, gamewidth/2, gameheight/8], "Player vs Player")

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        screen.fill((50, 50, 50))
        pygame.draw.rect(screen, [35, 35, 35], [0, 0, gamewidth, gameheight], 10)
        text(screen, [15, 15, 15], [gamewidth/2, gameheight/8], int(150/1080*gameheight), "Chess", font, True)

        if escButton.active():
            pygame.quit()
            quit()

        if pvpButton.active():
            stuff, information = settings("pvp")
            if stuff:
                carryon = True
                while carryon:
                    carryon = main(stuff, information)

        pygame.display.update()


def customBoard(customArray=None):
    thisBoardRect = [230/1920*gamewidth, 175/1080*gameheight, 800/1920*gamewidth, 800/1080*gameheight]
    boardImage = genBoardImage([int(thisBoardRect[2]), int(thisBoardRect[3])])
    piecesRect = [1100/1920*gamewidth, 175/1080*gameheight, 250/1920*gamewidth, 750/1080*gameheight]
    piecesImages = pygame.Surface([piecesRect[2], piecesRect[3]], pygame.SRCALPHA, 32).convert_alpha()
    escButton = Button([6, 6, 100 / 1920 * gamewidth, 50 / 1080 * gameheight], "Back")

    orderX = {"w": 0, "b": piecesRect[2]/2}
    orderY = {"Pawn": 0, "Knight": piecesRect[3]/6, "Bishop": piecesRect[3]/3,
              "Castle": piecesRect[3]/2, "Queen": piecesRect[3]/6*4, "King": piecesRect[3]/6*5}

    for image in os.listdir("pieces"):
        image = image[:-4]
        name, side = image[1:], image[0]
        x, y = orderX[side], orderY[name]
        newImage = pygame.transform.scale(loadImage(image, "pieces"), [int(piecesRect[2]/2 - piecesRect[2]/10), int(piecesRect[3]/6 - piecesRect[3]/60)])
        piecesImages.blit(newImage, [x + piecesRect[2]/20, y + piecesRect[3]/120])

    if customArray is None:
        customArray = [[Piece(None, i, j, thisBoardRect[2]/8, thisBoardRect[3]/8, thisBoardRect) for i in range(8)] for j in range(8)]
    cbpp = CustomBoard_PiecePlacement()
    saveButton = Button([1400/1920*gamewidth, 185/1080*gameheight, 400/1920*gamewidth, 100/1080*gameheight], "Save Board")
    loadButton = Button([1400 / 1920 * gamewidth, 720 / 1080 * gameheight, 400 / 1920 * gamewidth, 100 / 1080 * gameheight], "Load Board")
    useButton = Button([1400/1920*gamewidth, 840/1080*gameheight, 400/1920*gamewidth, 100/1080*gameheight], "Use Board")
    showRect = None
    while True:
        rect = None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            if event.type == pygame.KEYDOWN:
                if event.key == 27:
                    return None

        mousepos, mousepress = getmouse()
        if mousepress[0]:
            if not pointInRect(mousepos, piecesRect) and not pointInRect(mousepos, thisBoardRect):
                showRect = None

        if pointInRect(mousepos, piecesRect):
            i, j = int((mousepos[0] - piecesRect[0])/(piecesRect[2]/2)), int((mousepos[1] - piecesRect[1])/(piecesRect[3]/6))
            rect = [i*piecesRect[2]/2 + piecesRect[0], j*piecesRect[3]/6 + piecesRect[1], piecesRect[2]/2, piecesRect[3]/6]
            showRect = rect
            if mousepress[0]:
                side = {0: "w", 1: "b"}[i]
                name = {0: "Pawn", 1: "Knight", 2: "Bishop", 3: "Castle", 4: "Queen", 5: "King"}[j]
                cbpp.change(side + name)

        elif pointInRect(mousepos, thisBoardRect):
            if cbpp.piece is not None and mousepress[0]:
                i, j = int((mousepos[0] - thisBoardRect[0]) / (thisBoardRect[2] / 8)), int((mousepos[1] - thisBoardRect[1]) / (thisBoardRect[3] / 8))
                customArray[j][i].change(cbpp.piece)

            if mousepress[2]:
                i, j = int((mousepos[0] - thisBoardRect[0]) / (thisBoardRect[2] / 8)), int((mousepos[1] - thisBoardRect[1]) / (thisBoardRect[3] / 8))
                customArray[j][i].change(None)

        screen.fill((50, 50, 50))
        pygame.draw.rect(screen, [35, 35, 35], [0, 0, gamewidth, gameheight], 10)
        text(screen, [15, 15, 15], [gamewidth / 2, gameheight / 16], int(150/1080*gameheight), "Custom Board", font, True)
        screen.blit(boardImage, [thisBoardRect[0], thisBoardRect[1]])
        pygame.draw.rect(screen, [15, 15, 15], thisBoardRect, 5)
        screen.fill([75, 75, 75], piecesRect)
        
        if rect is not None:
            pygame.draw.rect(screen, [100, 100, 100], rect)
        elif showRect is not None:
            pygame.draw.rect(screen, [100, 100, 100], showRect)

        screen.blit(piecesImages, [piecesRect[0], piecesRect[1]])
        pygame.draw.rect(piecesImages, [35, 35, 35], [0, 0, piecesRect[2], piecesRect[3]], 10)

        for row in customArray:
            for piece in row:
                piece.render()

        if escButton.active():
            return None

        badThings = []
        kings = [0, 0]
        for row in customArray:
            for piece in row:
                if piece.name == "wKing": kings[0] += 1
                elif piece.name == "bKing": kings[1] += 1

        for num, side in zip([0, 1], ["White", "Black"]):
            if not kings[num]:
                badThings.append("{} King needed".format(side))
            elif kings[num] == 2:
                badThings.append("1 {} King only".format(side))

        y = 300/1080*gameheight
        for problem in badThings:
            text(screen, [5, 5, 5], [1400/1920*gamewidth, y], int(50/1080*gameheight), problem, font, False)
            y += 60/1080*gameheight

        if len(badThings) > 0:
            useButton.words = "Denied"
        else:
            useButton.words = "Use Board"

        if useButton.active() and len(badThings) == 0:
            screen.fill([50, 50, 50])
            return customArray

        if len(badThings) > 0:
            saveButton.words = "Save Denied"
        else:
            saveButton.words = "Save Board"

        if saveButton.active() and len(badThings) == 0:
            filename = saveGUI("customBoards")
            saveArray = [[piece.name for piece in row] for row in customArray]
            if not os.path.exists("customBoards"):
                os.mkdir("customBoards")

            with open("{}/{}.pkl".format("customBoards", filename), "wb") as file:
                pk.dump(saveArray, file, pk.HIGHEST_PROTOCOL)

        if loadButton.active():
            result = loadGameGUI(customArray, "customBoards")
            if result is not None:
                customArray = result

        pygame.display.update()


def saveGUI(folder):
    background = screen.copy()
    boxRect = [gamewidth / 4, gameheight / 2 - gameheight / 8, gamewidth / 2, gameheight / 4]
    nameBox = TextBox([boxRect[0], boxRect[1], boxRect[2], boxRect[3] / 3])
    save = Button([boxRect[0], boxRect[1] + boxRect[3] / 3, boxRect[2] / 2, boxRect[3] / 3 * 2], "Save")
    back = Button([boxRect[0] + boxRect[2] / 2, boxRect[1] + boxRect[3] / 3, boxRect[2] / 2, boxRect[3] / 3 * 2], "Back")

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        screen.blit(background, [0, 0])
        screen.fill([75, 75, 75], boxRect)

        if nameBox.text + ".pkl" in os.listdir(folder):
            save.words = "Filename Taken!"
            save.render(save.col1)
        else:
            if save.active() and len(nameBox.text) > 0:
                return nameBox.text

        if back.active():
            return False

        pygame.draw.rect(screen, [15, 15, 15], boxRect, 5)
        nameBox.active()

        pygame.display.update()


def loadGameGUI(customArray, folder):
    if not os.path.exists(folder):
        os.mkdir(folder)

    boxRect = [gamewidth / 8, gameheight / 8, 1440 / 1920 * gamewidth, 720 / 1080 * gameheight]
    singleBoxDim = [int(180 / 1920 * gamewidth), int(180 / 1080 * gameheight)]
    selectRect = [boxRect[0], boxRect[1], boxRect[2], boxRect[3] - singleBoxDim[1]]

    boardsImage, boards, information = loadCustomBoards(singleBoxDim, folder)

    background = screen.copy()
    loadBut = Button([boxRect[0], boxRect[1] + boxRect[3] - singleBoxDim[1] / 2, boxRect[2] / 2, singleBoxDim[1] / 2], "Load {}".format(folder))
    backBut = Button([boxRect[0] + boxRect[2] / 2, boxRect[1] + boxRect[3] - singleBoxDim[1], boxRect[2] / 2 - boxRect[2] / 16, singleBoxDim[1] / 2], "Back")
    delBut = Button([boxRect[0] + boxRect[2] / 2, boxRect[1] + boxRect[3] - singleBoxDim[1] / 2, boxRect[2] / 2 - boxRect[2] / 16, singleBoxDim[1] / 2], "Back")
    upBut = Button([boxRect[0] + boxRect[2] - boxRect[2] / 16, boxRect[1] + boxRect[3] - singleBoxDim[1], boxRect[2] / 16, singleBoxDim[1] / 2], "/\\")
    downBut = Button([boxRect[0] + boxRect[2] - boxRect[2] / 16, boxRect[1] + boxRect[3] - singleBoxDim[1] / 2, boxRect[2] / 16, singleBoxDim[1] / 2], "\\/")
    textBoxRect = [boxRect[0], boxRect[1] + boxRect[3] - singleBoxDim[1], boxRect[2] / 2, singleBoxDim[1] / 2]
    selected, loading, showStart = None, True, 0
    while loading:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if not pointInRect(event.pos, boxRect):
                    selected = None

        mousepos, mousepress = getmouse()

        screen.blit(background, [0, 0])
        screen.fill([75, 75, 75], boxRect)

        if backBut.active():
            customArray = None
            loading = False

        if selected is None:
            loadBut.words = "Select Board"
            delBut.words = "Select Board"
        else:
            loadBut.words = "Load {}".format(folder)
            delBut.words = "Delete Board"
            text(screen, [15, 15, 15], [textBoxRect[0] + textBoxRect[2] / 2, textBoxRect[1] + textBoxRect[3] / 2], int(textBoxRect[3] / 2), os.listdir(folder)[selected][:-4], font, True)

        if loadBut.active() and selected is not None:
            if customArray is None:
                customArray = information
            else:
                for j, row in enumerate(boards[selected]):
                    for i, piece in enumerate(row):
                        customArray[j][i].change(piece)
            loading = False

        if delBut.active() and selected is not None:
            os.remove(os.path.join(folder, os.listdir(folder)[selected]))
            boardsImage, boards, information = loadCustomBoards(singleBoxDim, folder)
            selected = None

        if showStart == 0:
            upBut.render([20, 20, 20])
        else:
            if upBut.active():
                showStart -= 8
                if showStart < 0:
                    showStart = 0

        if len(boards) - showStart <= 24:
            downBut.render([20, 20, 20])
        else:
            if downBut.active():
                showStart += 8
                if showStart > len(boards) - 24:
                    showStart = len(boards) - 24

        if len(boards) == 0:
            text(screen, [25, 25, 25], [selectRect[0] + selectRect[2] / 2, selectRect[1] + selectRect[3] / 2],
                 int(selectRect[3] / 8), folder + " file is Empty", font, True)

        else:
            x, y = boxRect[0], boardRect[1]
            for i, board in enumerate(boardsImage):
                if y < boxRect[1] + selectRect[3] and i >= showStart:

                    if pointInRect(mousepos, [x, y, singleBoxDim[0], singleBoxDim[1]]) or i == selected:
                        screen.fill([5, 5, 5], [x, y, singleBoxDim[0], singleBoxDim[1]])
                        if mousepress[0]:
                            selected = i

                    screen.blit(board, [x + singleBoxDim[0] / 32, y + singleBoxDim[1] / 32])

                    x += singleBoxDim[0]
                    if x >= boxRect[0] + boxRect[2]:
                        x = boxRect[0]
                        y += singleBoxDim[1]

        pygame.draw.rect(screen, [35, 35, 35], boxRect, 3)
        pygame.draw.rect(screen, [35, 35, 35], selectRect, 3)
        pygame.draw.line(screen, [35, 35, 35], [selectRect[0] + selectRect[2] / 2, selectRect[1] + selectRect[3]], [selectRect[0] + selectRect[2] / 2, boxRect[1] + boxRect[3]], 3)
        pygame.draw.line(screen, [35, 35, 35], [boxRect[0], boxRect[1] + boxRect[3] - singleBoxDim[1] / 2], [boxRect[0] + boxRect[2] - boxRect[2] / 16, boxRect[1] + boxRect[3] - singleBoxDim[1] / 2], 3)
        pygame.display.update()

    return customArray


def loadCustomBoards(singleBoxDim, folder):
    smallBoardImage = genBoardImage(singleBoxDim)
    boardsImage, boards, information = [], [], None
    for fileName in os.listdir(folder):
        if fileName[-4:] == ".pkl":
            boardSurf = pygame.Surface(singleBoxDim)
            with open("{}/{}".format(folder, fileName), "rb") as file:
                board = pk.load(file)
                if folder == "saves":
                    information = board
                    board = board["array"]
                else:
                    information = None

                boards.append(board)
                boardSurf.blit(smallBoardImage, [0, 0])
                for j, row in enumerate(board):
                    for i, piece in enumerate(row):
                        if piece is not None:
                            pieceImage = pygame.transform.scale(loadImage(piece, "pieces"), [int(singleBoxDim[0] / 8 - singleBoxDim[0] / 32), int(singleBoxDim[1] / 8 - singleBoxDim[1] / 32)])
                            pieceImageRect = pieceImage.get_rect()
                            pieceImageRect.center = [i * singleBoxDim[0] / 8 + singleBoxDim[0] / 16, j * singleBoxDim[1] / 8 + singleBoxDim[1] / 16]
                            boardSurf.blit(pieceImage, pieceImageRect)

            boardSurf = pygame.transform.scale(boardSurf, [int(singleBoxDim[0] - singleBoxDim[0] / 16), int(singleBoxDim[1] - singleBoxDim[1] / 16)])
            boardsImage.append(boardSurf)

    return boardsImage, boards, information


def settings(game):
    escButton = Button([6, 6, 100/1920*gamewidth, 50/1080*gameheight], "Menu")
    continueButton = Button([gamewidth/2 - gamewidth/4, gameheight - gameheight/8, gamewidth/2, gameheight/16], "--->")
    autoQueenButton = BooleanButton([120/1920*gamewidth, 560/1080*gameheight, 70/1920*gamewidth, 40/1920*gamewidth])
    allowBack = BooleanButton([325/1920*gamewidth, 560/1080*gameheight, 70/1920*gamewidth, 40/1920*gamewidth], True)
    allowEnPassent = BooleanButton([530/1920*gamewidth, 560/1080*gameheight, 70/1920*gamewidth, 40/1920*gamewidth], True)
    player1 = [numBox([350/1920*gamewidth, 200/1080*gameheight, 150/1920*gamewidth, 60/1080*gameheight], 0, 23, 0),
               numBox([575/1920*gamewidth, 200/1080*gameheight, 150/1920*gamewidth, 60/1080*gameheight], 0, 59, 10),
               numBox([800/1920*gamewidth, 200/1080*gameheight, 150/1920*gamewidth, 60/1080*gameheight], 0, 59, 0)]
    p1Controls = [Button([x / 1920 * gamewidth, 270 / 1080 * gameheight, 70 / 1920 * gamewidth, 45 / 1080 * gameheight], ting) for x, ting in zip([350, 430, 575, 655, 800, 880], ["+", "-", "+", "-", "+", "-"])]
    name1 = NameReview([1050/1920*gamewidth, 180/1080*gameheight, 800/1920*gamewidth, 100/1080*gameheight], "White", [[245, 245, 245], [185, 185, 185]])

    player2 = [numBox([350/1920*gamewidth, 350/1080*gameheight, 150/1920*gamewidth, 60/1080*gameheight], 0, 23, 0),
               numBox([575/1920*gamewidth, 350/1080*gameheight, 150/1920*gamewidth, 60/1080*gameheight], 0, 59, 10),
               numBox([800/1920*gamewidth, 350/1080*gameheight, 150/1920*gamewidth, 60/1080*gameheight], 0, 59, 0)]
    p2Controls = [Button([x / 1920 * gamewidth, 420 / 1080 * gameheight, 70 / 1920 * gamewidth, 45 / 1080 * gameheight], ting) for x, ting in zip([350, 430, 575, 655, 800, 880], ["+", "-", "+", "-", "+", "-"])]
    name2 = NameReview([1050 / 1920 * gamewidth, 340 / 1080 * gameheight, 800 / 1920 * gamewidth, 100 / 1080 * gameheight], "Black", [[15, 15, 15], [35, 35, 35]])

    loadButton = Button([gamewidth/2 - gamewidth/4, gameheight - gameheight/16*3 - 10/1080*gameheight, gamewidth/2, gameheight/16], "Load Game")
    customButton = Button([gamewidth/2 - gamewidth/4, gameheight - gameheight/4 - 20/1080*gameheight, gamewidth/2, gameheight/16], "Custom Board")
    array, information = None, None
    while True:
        background = screen.copy()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if array is not None:
                        array = arrayToWord(array)
                    return saveSettings(player1, player2, autoQueenButton, allowBack, array, name1, name2, allowEnPassent), information

        renderSettings_Images()

        if continueButton.active():
            if array is not None:
                array = arrayToWord(array)
            return saveSettings(player1, player2, autoQueenButton, allowBack, array, name1, name2, allowEnPassent), information

        if escButton.active():
            return False, information

        if loadButton.active():
            result = loadGameGUI(array, "saves")
            if result is not None:
                information = result

        if customButton.active():
            array = customBoard(array)

        autoQueenButton.activate()
        allowBack.activate()
        allowEnPassent.activate()

        for box in player1:
            box.active(background)

        for box in player2:
            box.active(background)

        for p, pc in zip([player1, player2], [p1Controls, p2Controls]):
            for i, add in enumerate(pc):
                clicked = add.active()
                if clicked:
                    k = -1 if (i+1) % 2 == 0 else 1
                    p[i//2].number += k

        name1.active(name2)
        name2.active(name1)

        pygame.display.update()


def saveSettings(player1, player2, autoQueen, allowBack, array, name1, name2, allowEnPassent):
    times = [0, 0]
    count = 0
    for time, p in zip(times, [player1, player2]):
        time += p[0].number * 3600
        time += p[1].number * 60
        time += p[2].number
        times[count] = time
        count += 1

    if allowEnPassent.current:
        enpassent = [[False for i in range(8)] for j in range(8)]
    else:
        enpassent = False

    stuff = {"time1": times[0], "time2": times[1], "autoQueen": autoQueen.current, "allowBack": allowBack.current,
             "array": array, "name1": name1.text, "name2": name2.text, "enPassent": enpassent}
    return stuff


def renderSettings_Images():
    screen.fill((50, 50, 50))
    pygame.draw.rect(screen, [35, 35, 35], [0, 0, gamewidth, gameheight], 10)
    text(screen, [15, 15, 15], [gamewidth / 2, gameheight / 16], int(150/1080*gameheight), "Game Settings", font, True)

    text(screen, [15, 15, 15], [50 / 1920 * gamewidth, 185 / 1080 * gameheight], int(60/1080*gameheight), "Player 1", font, False)
    text(screen, [15, 15, 15], [50 / 1920 * gamewidth, 335 / 1080 * gameheight], int(60/1080*gameheight), "Player 2", font, False)

    text(screen, [15, 15, 15], [165/1920 * gamewidth, 500/1080*gameheight], int(30/1080*gameheight), "Auto", font, True)
    text(screen, [15, 15, 15], [165/1920*gamewidth, 525/1080*gameheight], int(30/1080*gameheight), "Pawn -> Queen", font, True)

    text(screen, [15, 15, 15], [360 / 1920 * gamewidth, 525 / 1080 * gameheight], int(30/1080*gameheight), "Allow Back", font, True)

    text(screen, [15, 15, 15], [570 / 1920 * gamewidth, 525 / 1080 * gameheight], int(30 / 1080 * gameheight), "Allow EnPassent", font, True)

    for y in [200/1080*gameheight, 350/1080*gameheight]:
        text(screen, [15, 15, 15], [510/1920*gamewidth, y - 13], int(60/1080*gameheight), "h", font, False)
        text(screen, [15, 15, 15], [730/1920*gamewidth, y - 13], int(60/1080*gameheight), "m", font, False)
        text(screen, [15, 15, 15], [960/1920*gamewidth, y - 13], int(60/1080*gameheight), "s", font, False)


info = Info()
def main(stuff, information):
    array = [[Piece(startLayout[j][i], i, j, boardRect[2]/8, boardRect[3]/8) for i in range(len(startLayout[0]))] for j in range(len(startLayout))]
    array = info.reset(stuff, array)
    if information is not None:
        info.load(array, information)

    board = genBoardImage([boardRect[2], boardRect[3]])
    moving, dobreak = None, False
    info.endGame(array)
    while True:
        end = False
        # Draw Screen Background
        screen.fill((50, 50, 50))
        pygame.draw.rect(screen, [35, 35, 35], [0, 0, gamewidth, gameheight], 10)
        screen.blit(board, [boardRect[0], boardRect[1]])
        pygame.draw.rect(screen, [35, 35, 35], boardRect, 5)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        prarray = []
                        for row in array:
                            prarray.append([])
                            for piece in row:
                                prarray[-1].append(piece.name)
                            print(prarray[-1])

            if event.type == pygame.MOUSEBUTTONDOWN:
                if pointInRect(event.pos, boardRect):
                    for j, row in enumerate(array):
                        for i, piece in enumerate(row):
                            click, pieceName = piece.clicked(event.pos)
                            if click and info.side != pieceName[0]:
                                click = not click

                            if click:
                                piece.show = False
                                moving = MovingPiece(pieceName, i, j, array)
                                break
                        if click:
                            break

        for row in array:
            for cell in row:
                cell.render()

        array = info.active(array)
        if True in info.CHEAT:
            if info.CHEAT[0]:
                side = info.name2
            else:
                side = info.name1
            winBy = "cheating!"
            break

        elif True in info.MATE:
            if info.MATE[1]:
                side = info.name1
            else:
                side = info.name2
            winBy = "Checkmate"
            break

        elif True in info.STALE:
            winBy = "Stalemate"
            break

        elif info.DRAW:
            winBy = "Draw"
            break

        for i, theTime in enumerate(info.times[:]):
            if theTime <= -1:
                moving, side = None, {0: info.name1, 1: info.name2}[i]
                end = True
                winBy = "Time"
                break

        if moving is not None:
            array, delete = moving.active(array)
            if delete:
                moving = None

        pygame.display.update()
        if end:
            break
    pygame.display.update()

    prevPage = screen.copy()
    resultsPage = pygame.Surface([gamewidth, gameheight], pygame.SRCALPHA, 32).convert_alpha()
    transparent, xs = 0, [boardRect[0] + boardRect[2]/2 - 1000, boardRect[0] + boardRect[2]/2 + 1000]
    update = False
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_x or event.key == pygame.K_ESCAPE:
                    return False

            if event.type == pygame.MOUSEBUTTONDOWN:
                return True

        if transparent < 175:
            transparent += 3

            resultsPage.fill((236, 224, 200, transparent), boardRect)
            screen.blit(prevPage, [0, 0])
            screen.blit(resultsPage, [0, 0])
            newScreen = screen.copy()
        else:
            screen.blit(newScreen, (0, 0))

        if transparent >= 175:
            if winBy == "Stalemate" or winBy == "Draw":
                tex = "Game Over - {}".format(winBy)
            else:
                tex = "{} won by {}".format(side, winBy)
            text(screen, [5, 5, 5], [xs[0], boardRect[1] + boardRect[3]/2 - 50], 50, tex, font, True)
            text(screen, [5, 5, 5], [xs[1], boardRect[1] + boardRect[3]/2], 40, "Press Esc to return to menu", font, True)
            text(screen, [5, 5, 5], [xs[0], boardRect[1] + boardRect[3]/2 + 40], 40, "Click anywhere to play again", font, True)

            if xs[0] < boardRect[0] + boardRect[2]/2:
                xs[0] += 5
            if xs[1] > boardRect[0] + boardRect[2]/2:
                xs[1] -= 5
            else:
                update = True

        if update:
            pygame.display.update()
        else:
            pygame.display.update(boardRect)


if __name__ == "__main__":
    menu()
