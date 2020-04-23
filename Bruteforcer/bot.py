import random

from battlehack20.stubs import *

# This is an example bot written by the developers!
# Use this to help write your own code, or run it against your bot to see how well you can do!

DEBUG = 1
board_size = -1
team = -1
forward = -1
backward = -1
opp_team = -1

lastpos = (-1, -1)
posRow = -1
posCol = -1
standstillTurns = 0
homeRow = -1
enemyHomeRow = -1
turnsLived = 0


spawn_desires =      [1,4,7,7,5,1,0,0,0,0,0,0,0,0,0,0,0,0,0]  #hardcoded push on the left, as a sort of 'communicated strategy'
extra_push_desires = [ 1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0]


def dlog(str):
    if DEBUG > 0:
        log(str)


def check_space_wrapper(r, c, board_size):
    # check space, except doesn't hit you with game errors
    if r < 0 or c < 0 or c >= board_size or r >= board_size:
        return False
    try:
        return check_space(r, c)
    except:
        return None

def isEnemy(r,c):
    if r < 0 or c < 0 or c >= board_size or r >= board_size:
        return False
    try:
        return check_space(r, c) == opp_team
    except:
        return False


def isFriend(r, c):
    if r < 0 or c < 0 or c >= board_size or r >= board_size:
        return False
    try:
        return check_space(r, c) == team
    except:
        return False


def turn():
    """
    MUST be defined for robot to run
    This function will be called at the beginning of every turn and should contain the bulk of your robot commands
    """
    global board_size, forward, backward, team, opp_team, lastpos, posRow, posCol, standstillTurns, homeRow, enemyHomeRow, turnsLived, spawn_desires

    # dlog('Starting Turn!')
    board_size = get_board_size()

    team = get_team()
    opp_team = Team.WHITE if team == Team.BLACK else team.BLACK
    # dlog('Team: ' + str(team))

    robottype = get_type()
    # dlog('Type: ' + str(robottype))
    turnsLived += 1

    if team == Team.WHITE:
        homeRow = 0
        enemyHomeRow = board_size - 1
        forward = 1
        backward = -1
    else:
        homeRow = board_size - 1
        enemyHomeRow = 0
        forward = -1
        backward = 1

    spawn_desires[board_size-1] = -2

    if robottype == RobotType.PAWN:
        lastpos = (posRow,posCol)
        posRow, posCol = get_location()
        # dlog('My location is: ' + str(row) + ' ' + str(col))

        if lastpos[0] == posRow and lastpos[1] == posCol:
            standstillTurns += 1
        else:
            standstillTurns = 0


        bestmove = -1
        bestscore = evalMove(posRow,posCol,0)


        if posRow + forward != -1 and posRow + forward != board_size and not check_space_wrapper(posRow + forward, posCol, board_size):
            score = evalMove(posRow+forward,posCol,0)
            if score > bestscore:
                bestscore = score
                bestmove = 0

        if check_space_wrapper(posRow + forward, posCol + 1, board_size) == opp_team: # up and right
            score = evalMove(posRow + forward, posCol+1, 1)
            if score > bestscore:
                bestscore = score
                bestmove = 1

        if check_space_wrapper(posRow + forward, posCol - 1, board_size) == opp_team: # up and left
            score = evalMove(posRow + forward, posCol + 1, 1)
            if score > bestscore:
                bestmove = 2

        if bestmove == 0:
            move_forward()
        elif bestmove == 1:
            capture(posRow + forward, posCol + 1)
        elif bestmove == 2:
            capture(posRow + forward, posCol - 1)

    else:
        bestSpawnScore = -5000
        bestSpawn = -1

        for i in range(board_size):
            if not check_space(homeRow, i):
                score = evalSpawn(i)
                if score > bestSpawnScore:
                    bestSpawn = i
                    bestSpawnScore = score
        if bestSpawn >= 0:
            spawn(homeRow, bestSpawn)


    # bytecode = get_bytecode()
    # dlog('Done! Bytecode left: ' + str(bytecode))


def evalMove(moveRow,moveCol, isCapture):
    global team
    global board_size, turnsLived, standstillTurns

    score = 0

    if team == Team.WHITE:
        distanceMySide = moveRow
        distanceTheirSide = (board_size - moveRow) - 1
    else:
        distanceMySide = (board_size - moveRow) - 1
        distanceTheirSide = moveRow

    score += distanceMySide
    rightcapturable = isEnemy(moveRow + forward, moveCol + 1)
    leftcapturable = isEnemy(moveRow + forward, moveCol - 1)

    checkRight = False
    checkLeft = False

    captureBalance = 0
    if isCapture:
        captureBalance += 1
        if moveCol == posCol + 1:
            checkRight = True
        else:
            checkLeft = True
    else:
        checkLeft = True
        checkRight = True


    if checkLeft and isFriend(moveRow + backward, moveCol-1):
        if isEnemy(moveRow, moveCol-2):
            captureBalance += 0.5
        else:
            captureBalance += 1

        if isFriend(moveRow + backward * 2, moveCol - 1):
            captureBalance += 0.5

    if checkRight and isFriend(moveRow + backward, moveCol+1):
        if isEnemy(moveRow, moveCol+2):
            captureBalance += 0.5
        else:
            captureBalance += 1

        if isFriend(moveRow + backward * 2, moveCol + 1):
            captureBalance += 0.5


    if rightcapturable:
        captureBalance -= 1

    if leftcapturable:
        captureBalance -= 1

    if isEnemy(moveRow + forward * 2, moveCol + 1):
        captureBalance -= 0.5
    if isEnemy(moveRow + forward * 2, moveCol - 1):
        captureBalance -= 0.5

    captureScore = 0
    if isCapture:
        captureScore = 200 + distanceTheirSide * 2
        score += captureScore


    if rightcapturable or leftcapturable:
        #Just don't even think about pushing
        if captureBalance < 0.5 and not isCapture and standstillTurns < 250:
            score-=1000

        # Determine whether pushing is worth it
        if captureBalance < 1.5:

            if extra_push_desires[moveCol] > 0:

                avoidcapture = (-60 * (captureBalance - 1.5)) - standstillTurns * 0.2

                if not isCapture:
                    avoidcapture += 50

                if turnsLived < 200:
                    avoidcapture += 30


                if isFriend(posRow + backward, posCol):
                    avoidcapture -= (20 + standstillTurns * 0.1)
                    if isFriend(posRow + backward * 2, posCol):
                        avoidcapture -= (10 + standstillTurns * 0.1)

                if isFriend(posRow + backward, posCol+1):
                    avoidcapture -= 10
                    if isFriend(posRow + backward * 2, posCol+1):
                        avoidcapture -= 5

                if isFriend(posRow + backward, posCol-1):
                    avoidcapture -= 10
                    if isFriend(posRow + backward * 2, posCol-1):
                        avoidcapture -= 5


                if rightcapturable and leftcapturable:
                    avoidcapture += 20

                avoidcapture += distanceMySide * 3

                avoidcapture -= captureScore * 0.3

                score -= max(0, avoidcapture)
            else:
                score -= 140
                if rightcapturable and leftcapturable:
                    score -= 20

        else:
            score += 5 * captureBalance




    #cover for a friend in danger
    if isFriend(moveRow + forward, moveCol + 1):
        if isEnemy(moveRow + forward * 2, moveCol) or isEnemy(moveRow + forward * 2, moveCol + 2):
            score += 10

    if isFriend(moveRow + forward, moveCol - 1):
        if isEnemy(moveRow + forward * 2, moveCol) or isEnemy(moveRow + forward * 2, moveCol - 2):
            score += 10


    #block passage of enemy
    if isEnemy(moveRow + forward * 2, moveCol - 1):
        score += 2
    if isEnemy(moveRow + forward * 2, moveCol + 1):
        score += 2


    return score


def evalSpawn(spawnCol):
    score = 0

    if isEnemy(homeRow + forward,spawnCol):
        score += 1000

    if isEnemy(homeRow + forward,spawnCol-1):   #never ever! may give them a win point when they wouldnt otherwise be able to get one
        score -= 10000

    if isEnemy(homeRow + forward, spawnCol+1):  #never ever! may give them a win point when they wouldnt otherwise be able to get one
        score -= 10000

    if isEnemy(homeRow + forward * 2, spawnCol):
        score += 40

    if isEnemy(homeRow + forward * 2, spawnCol-1):
        score += 60

    if isEnemy(homeRow + forward * 2, spawnCol + 1):
        score += 60

    if isFriend(enemyHomeRow,spawnCol):
        score -= 10


    friendCount = 0
    enemyCount = 0
    firstFound = -1

    friendCountLeft = 0
    enemyCountLeft = 0
    friendCountRight = 0
    enemyCountRight = 0

    for i in range(homeRow,enemyHomeRow,forward):
        if isFriend(i, spawnCol):
            friendCount += 1
            if firstFound == -1:
                firstFound = 0
        if isEnemy(i, spawnCol):
            enemyCount += 1
            if firstFound == -1:
                firstFound = 1

        if isFriend(i, spawnCol -1):
            friendCountLeft += 1
        if isEnemy(i, spawnCol - 1):
            enemyCountLeft += 1

        if isFriend(i, spawnCol + 1):
            friendCountRight += 1
        if isEnemy(i, spawnCol + 1):
            enemyCountRight += 1


    if enemyCount >= 1 and firstFound != 0:
        score += 15

    score -= friendCount * 2
    score += enemyCount

    score -= friendCountLeft * 0.5
    score -= friendCountRight * 0.5

    score += min(6, enemyCountLeft + enemyCountRight) * 1.5

    # score -= abs( spawnCol - board_size/2) * 0.1

    score += spawn_desires[spawnCol]

    return score






def max(a,b):
    if a > b:
        return a
    return b

def min(a,b):
    if a < b:
        return a
    return b

def abs(a):
    if a < 0: return -a
    return a