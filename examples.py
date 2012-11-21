import random
import logging
import math

from api import Commander
from api import commands
from aigd import Vector2


def contains(area, position):
    start, finish = area
    return position.x >= start.x and position.y >= start.y and position.x <= finish.x and position.y <= finish.y


class RandomCommander(Commander):
    """
    Sends everyone to randomized positions or a random choice of flag location.  The behavior of returning the flag
    to the home base after capturing it is purely emergent!
    """

    def tick(self):
        """Process all the bots that are done with their orders and available for taking commands."""

        # The 'bots_available' list is a dynamically calculated list of bots that are done with their commands.
        for bot in self.game.bots_available:
            # Determine a place to run randomly...
            target = random.choice(
                          # 1) Either a random choice of *current* flag locations, ours or theirs.
                          [f.position for f in self.game.flags.values()]
                          # 2) Or a random choice of the goal locations for returning flags.
                        + [s for s in self.level.flagScoreLocations.values()]
                          # 3) Or a random position in the entire level, one that's not blocked.
                        + [self.level.findRandomFreePositionInBox(self.level.area)]
            )
            # Pick random movement style between going fast or moving carefully.
            commandType = random.choice([commands.Attack, commands.Charge])
            if target:
                self.issue(commandType, bot, target, description = 'random')


class AxedaCommander(Commander):
    
        
    """
    A Debug Commander
    """
    
    tickCount = 0
    
    logger = logging.getLogger('AISBox')
    hdlr = logging.FileHandler('C:\AISBox\CaptureTheFlag-sdk\Match.log')
    formatter = logging.Formatter('%(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr) 
    logger.setLevel(logging.INFO)    
    
    def captured(self):
        """Did this team cature the enemy flag?"""
        return self.game.enemyTeam.flag.carrier != None

    def initialize(self):
        self.logger.info("************************************************************************************")
        self.logger.info("************************************************************************************")
        self.logger.info("And so it begins...")
        self.logger.info("************************************************************************************")
        self.logger.info("************************************************************************************\n")
        self.logger.info("Level Info: ")
        self.logger.info("\tFiring Distance: %f",self.level.firingDistance)
        self.logger.info("\tMap Width,Height: %f,%f",self.level.height,self.level.width)
        self.logger.info("\tEnemy team size: %f",len(self.game.enemyTeam.members))
        self.logger.info("")
        self.verbose = True

    def tick(self):
                
        self.tickCount+=1
                
        """Process the bots that are waiting for orders, either send them all to attack or all to defend."""
        captured = self.captured()

        our_flag = self.game.team.flag.position
        their_flag = self.game.enemyTeam.flag.position
        their_base = self.level.botSpawnAreas[self.game.enemyTeam.name][0]

        if self.game.bots_available is not None or len(self.game.bots_available==1):
            self.logger.info('Turn %d: All of our bots are busy!',self.tickCount)
        else:
            self.logger.info(' =-=-=-=-=-=-=-=-=-=-=-=')
            self.logger.info('######## Turn %d ########',self.tickCount)
            self.logger.info(' =-=-=-=-=-=-=-=-=-=-=-=\n')

        buddySeesBot = False 

        # Only process bots that are done with their orders...
        for bot in self.game.bots_available:

            self.dumpBotInfo(bot)
            states = {0:'STATE_UNKNOWN',1:'STATE_IDLE',2:'STATE_DEFENDING',3:'STATE_MOVING',4:'STATE_ATTACKING',5:'STATE_CHARGING',6:'STATE_SHOOTING'}
            
            if bot.visibleEnemies is not None and len(bot.visibleEnemies) > 0:
                #self.logger.info("%d enemies spotted") % len(bot.visibleEnemies)
                for enemy in bot.visibleEnemies:
                    self.dumpEnemyInfo(bot,enemy,states)

            # check the relation of the bot to us
            
            self.logger.info(' ')
            self.logger.info('########################')
            self.logger.info(' ')
                
            # If this team has captured the flag, then tell this bot...
            if captured:
                target = self.game.team.flagScoreLocation
                # 1) Either run home, if this bot is the carrier or otherwise randomly.
                if bot.flag is not None or (random.choice([True, False]) and (target - bot.position).length() > 8.0):
                    self.issue(commands.Charge, bot, target, description = 'scrambling home')
                # 2) Run to the exact flag location, effectively escorting the carrier.
                else:
                    self.issue(commands.Attack, bot, self.game.enemyTeam.flag.position, description = 'defending flag carrier',
                               lookAt = random.choice([their_flag, our_flag, their_flag, their_base]))

            # In this case, the flag has not been captured yet so have this bot attack it!
            else:                
                ## pivot randomly to "sweep" the area every once in a while
                #if random.choice([False,True]):
                #    yChange = random.choice([-1.00,1.00])
                #    xChange = random.choice([1.00,-1.00])
                #    path = [bot.position - Vector2(xChange,yChange)]
                #    self.logger.info("Pivot time!")
                #    path.insert(1, bot.position + Vector2(xChange,yChange))
                #    path.insert(2, self.game.enemyTeam.flag.position)
                
                #else:
                path = [self.game.enemyTeam.flag.position]

                if contains(self.level.botSpawnAreas[self.game.team.name], bot.position) and random.choice([True, False]):
                    path.insert(0, self.game.team.flagScoreLocation)

                if bot.name == "Blue0" or bot.name == "Red0":
                    self.logger.info("Re-issuing defend")
                    self.issue(commands.Defend,bot,Vector2(random.choice([-0.5,0.5,-1.0,1.0]),random.choice([-0.5,0.5,-1.0,1.0])),"Where are the enemy?")
                else:                    
                    self.issue(commands.Attack, bot, path, description = 'attacking enemy flag',
                                    lookAt = random.choice([their_flag, our_flag, their_flag, their_base]))

    def dumpBotInfo(self,bot):
        botOrientation = self.reportOrientation(bot.facingDirection)
        self.logger.info('########################')
        self.logger.info('%s turn',bot.name)
        self.logger.info(' ')
        self.logger.info('Current Position')
        self.logger.info(' %f,%f',bot.position.x,bot.position.y)
        self.logger.info(botOrientation)

        if bot.flag is not None:
            self.logger.info('Flag %s',bot.flag.name)

        if bot.seenBy is not None:
            for spy in bot.seenBy:
                enemyOrientation = self.reportOrientation(spy.facingDirection)
                self.logger.info('')
                self.logger.info('\t====== Detected by Enemy ======')
                self.logger.info('\t%s',spy.name)
                self.logger.info('\t%s',enemyOrientation)
                self.logger.info('\t%s',self.reportPOV(botOrientation,enemyOrientation,True))
                self.logger.info('')    

        if bot.seenlast is not None:
            self.logger.info('Seen Last %s',bot.seenlast)

    def dumpEnemyInfo(self,bot,enemy,states):
        self.logger.info('\t====== Enemy Spotted ======')
        self.logger.info('\t%s',enemy.name)
        if enemy.state is not None:
            self.logger.info('\t%s',states[enemy.state])
        d = (bot.position - enemy.position)
        front = Vector2(d.x, d.y).normalized()
        enemyOrientation = self.reportOrientation(front)
        self.logger.info('\t%s',enemyOrientation)
        self.logger.info('\tDistance: %f',self.calculateDistance(bot.position,enemy.position))                
        self.logger.info(self.reportPOV(self.reportOrientation(bot.facingDirection),enemyOrientation,False))
        
        #self.logger.info('\tDirection:',front
        
    def calculateDistance(self,botPosition,enemyPosition):
        # positive/negative doesn't matter since we're squaring it
        deltaX = botPosition.x - enemyPosition.x
        deltaY = botPosition.y - enemyPosition.y
        return math.sqrt((deltaX*deltaX)+(deltaY*deltaY))
        
    def reportOrientation(self,orientation):
        orientLabel = "Facing: "
        
        if orientation.y < 0:
            orientLabel += "North"
        elif orientation.y > 0:
            orientLabel += "South"
        elif orientation.y == 0:
            orientLabel += "Center"
            
        if orientation.x < 0:
            orientLabel += "West"
        elif orientation.x > 0:
            orientLabel += "East"
        elif orientation.x == 0:
            orientLabel += "Center"           
            
        return orientLabel    
        
    def reportPOV(self,botOrientation,enemyOrientation,enemyMode):
        if botOrientation == enemyOrientation:
            if enemyMode:
                return "Enemy behind us!"
            else:
                return "We are behind the Enemy!"

        # check for opposites
        yMatch = botOrientation[:5] == enemyOrientation[:5]
        xMatch = botOrientation[5:5] == enemyOrientation[5:5]

        if (xMatch is True and yMatch is True):
                return "\tEnemy facing us!"
    
        return ""
    
class DefenderCommander(Commander):
    """
    Leaves everyone to defend the flag except for one lone guy to grab the other team's flag.
    """

    def initialize(self):
        self.attacker = None

    def tick(self):
        # TODO: When defender is down to the last bot that's attacking the flag, it'll end up ordering
        # the attacker to run all the way back from the flag to defend!
        if self.attacker and self.attacker.health <= 0:
            self.attacker = None

        for bot in self.game.bots_available:
            if (not self.attacker or self.attacker == bot) and len(self.game.bots_available) > 1:
                self.attacker = bot

                if bot.flag:
                    #bring it hooome
                    targetLocation = self.game.team.flagScoreLocation
                    self.issue(commands.Charge, bot, targetLocation, description = 'returning enemy flag!')

                else:
                    # find the closest flag that isn't ours
                    enemyFlagLocation = self.game.enemyTeam.flag.position
                    self.issue(commands.Charge, bot, enemyFlagLocation, description = 'getting enemy flag!')

            else:
                if self.attacker == bot:
                    self.attacker = None

                # defend the flag!
                targetPosition = self.game.team.flagScoreLocation
                targetMin = targetPosition - Vector2(8.0, 8.0)
                targetMax = targetPosition + Vector2(8.0, 8.0)
                if bot.flag:
                    #bring it hooome
                    targetLocation = self.game.team.flagScoreLocation
                    self.issue(commands.Charge, bot, targetLocation, description = 'returning enemy flag!')
                else:
                    if (targetPosition - bot.position).length() > 9.0 and  (targetPosition - bot.position).length() > 3.0 :
                        while True:
                            position = self.level.findRandomFreePositionInBox((targetMin,targetMax))
                            if position and (targetPosition - position).length() > 3.0:
                                self.issue(commands.Move, bot, position, description = 'defending around flag')
                                break
                    else:
                        self.issue(commands.Defend, bot, (targetPosition - bot.position), description = 'defending facing flag')



class BalancedCommander(Commander):
    """An example commander that has one bot attacking, one defending and the rest randomly searching the level for enemies"""

    def initialize(self):
        self.attacker = None
        self.defender = None
        self.verbose = False

        # Calculate flag positions and store the middle.
        ours = self.game.team.flag.position
        theirs = self.game.enemyTeam.flag.position
        self.middle = (theirs + ours) / 2.0

        # Now figure out the flaking directions, assumed perpendicular.
        d = (ours - theirs)
        self.left = Vector2(-d.y, d.x).normalized()
        self.right = Vector2(d.y, -d.x).normalized()
        self.front = Vector2(d.x, d.y).normalized()


    # Add the tick function, called each update
    # This is where you can do any logic and issue new orders.
    def tick(self):

        if self.attacker and self.attacker.health <= 0:
            # the attacker is dead we'll pick another when available
            self.attacker = None

        if self.defender and (self.defender.health <= 0 or self.defender.flag):
            # the defender is dead we'll pick another when available
            self.defender = None

        # In this example we loop through all living bots without orders (self.game.bots_available)
        # All other bots will wander randomly
        for bot in self.game.bots_available:           
            if (self.defender == None or self.defender == bot) and not bot.flag:
                self.defender = bot

                # Stand on a random position in a box of 4m around the flag.
                targetPosition = self.game.team.flagScoreLocation
                targetMin = targetPosition - Vector2(2.0, 2.0)
                targetMax = targetPosition + Vector2(2.0, 2.0)
                goal = self.level.findRandomFreePositionInBox([targetMin, targetMax])
                
                if (goal - bot.position).length() > 8.0:
                    self.issue(commands.Charge, self.defender, goal, description = 'running to defend')
                else:
                    self.issue(commands.Defend, self.defender, (self.middle - bot.position), description = 'turning to defend')

            elif self.attacker == None or self.attacker == bot or bot.flag:
                # Our attacking bot
                self.attacker = bot

                if bot.flag:
                    # Tell the flag carrier to run home!
                    target = self.game.team.flagScoreLocation
                    self.issue(commands.Move, bot, target, description = 'running home')
                else:
                    target = self.game.enemyTeam.flag.position
                    flank = self.getFlankingPosition(bot, target)
                    if (target - flank).length() > (bot.position - target).length():
                        self.issue(commands.Attack, bot, target, description = 'attack from flank', lookAt=target)
                    else:
                        flank = self.level.findNearestFreePosition(flank)
                        self.issue(commands.Move, bot, flank, description = 'running to flank')

            else:
                # All our other (random) bots

                # pick a random position in the level to move to                               
                box = min(self.level.width, self.level.height)
                target = self.level.findRandomFreePositionInBox((self.middle + box * 0.4, self.middle - box * 0.4))

                # issue the order
                if target:
                    self.issue(commands.Attack, bot, target, description = 'random patrol')

    def getFlankingPosition(self, bot, target):
        flanks = [target + f * 16.0 for f in [self.left, self.right]]
        options = map(lambda f: self.level.findNearestFreePosition(f), flanks)
        return sorted(options, key = lambda p: (bot.position - p).length())[0]