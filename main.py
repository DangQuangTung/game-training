
__author__ = "Rohit Rane"

import os
import sys
import pygame # type: ignore
import random
from pygame import *
import h5py
pygame.init()

scr_size = (width,height) = (600,300)
FPS = 60
gravity = 0.6

black = (0,0,0)
white = (255,255,255)
background_col = (235,235,235)

high_score = 0

#Các biến đã thêm của chúng tôi
desert = [None, None] #Tracks vị trí xương rồng (Tối đa hai xương rồng)
global distance #Biến toàn cầu theo dõi khoảng cách từ khủng long đến sa mạc[0]
distance = 0

restart = True # Đặt thời tiết hay không, chúng tôi muốn chương trình tự động khởi động lại
global isJumping #Có lẽ không cần thiết phải là toàn cầu, hãy theo dõi nếu khủng long đang nhảy
global iteration #Theo dõi số lần lặp hiện tại
iteration = 0

global jumpMemory # Mảng có kích thước động của các giá trị hành động nhảy
global noJumpMemory #Same nhưng đối với giá trị noJump-action
global lastRun #Tracks lần chạy cuối cùng, được sử dụng để đặt trọng số vào jumpMemory và noJumpMemory

SPREAD_PERCENT = .1

jumpMemory = []
noJumpMemory = []
lastRun = []

NUM_POINTS = 12 #Chúng tôi muốn bao nhiêu "điểm nhảy"
POINT_DISTANCE = 20 # Cách chúng tôi muốn các "điểm nhảy" (NHIỀU TRONG BỐN!)
global action #Bộ quyết định hành động toàn cầu được mô hình RF sử dụng
action = 0

global e #Theo dõi phần trăm cơ hội để dự đoán so với hành động ngẫu nhiên
e = 1
eGoal = 0 #Giá trị mà e sẽ bị giảm bởi eDecay cho đến khi nó đạt được
eDecay = .01 #Có bao nhiêu e phân rã mỗi lần lặp lại

for i in range(0, NUM_POINTS):#Tự động thay đổi kích thước mảng thành NUM_POINTS
    noJumpMemory.append(0)
    jumpMemory.append(0)
    lastRun.append(0)

screen = pygame.display.set_mode(scr_size)
clock = pygame.time.Clock()
pygame.display.set_caption("Khủng Long  ")

jump_sound = pygame.mixer.Sound('sprites/jump.wav')
die_sound = pygame.mixer.Sound('sprites/die.wav')
checkPoint_sound = pygame.mixer.Sound('sprites/checkPoint.wav')

def load_image(
    name,
    sizex=-1,
    sizey=-1,
    colorkey=None,
    ):

    fullname = os.path.join('sprites', name)
    image = pygame.image.load(fullname)
    image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey, RLEACCEL)

    if sizex != -1 or sizey != -1:
        image = pygame.transform.scale(image, (sizex, sizey))

    return (image, image.get_rect())

def load_sprite_sheet(
        sheetname,
        nx,
        ny,
        scalex = -1,
        scaley = -1,
        colorkey = None,
        ):
    fullname = os.path.join('sprites',sheetname)
    sheet = pygame.image.load(fullname)
    sheet = sheet.convert()

    sheet_rect = sheet.get_rect()

    sprites = []

    sizex = sheet_rect.width/nx
    sizey = sheet_rect.height/ny

    for i in range(0,ny):
        for j in range(0,nx):
            rect = pygame.Rect((j*sizex,i*sizey,sizex,sizey))
            image = pygame.Surface(rect.size)
            image = image.convert()
            image.blit(sheet,(0,0),rect)

            if colorkey is not None:
                if colorkey is -1:
                    colorkey = image.get_at((0,0))
                image.set_colorkey(colorkey,RLEACCEL)

            if scalex != -1 or scaley != -1:
                image = pygame.transform.scale(image,(scalex,scaley))

            sprites.append(image)

    sprite_rect = sprites[0].get_rect()

    return sprites,sprite_rect

def disp_gameOver_msg(retbutton_image,gameover_image):
    retbutton_rect = retbutton_image.get_rect()
    retbutton_rect.centerx = width / 2
    retbutton_rect.top = height*0.52

    gameover_rect = gameover_image.get_rect()
    gameover_rect.centerx = width / 2
    gameover_rect.centery = height*0.35

    screen.blit(retbutton_image, retbutton_rect)
    screen.blit(gameover_image, gameover_rect)

def extractDigits(number):
    if number > -1:
        digits = []
        i = 0
        while(number/10 != 0):
            digits.append(number%10)
            number = int(number/10)

        digits.append(number%10)
        for i in range(len(digits),5):
            digits.append(0)
        digits.reverse()
        return digits

class Dino():
    def __init__(self,sizex=-1,sizey=-1):
        global isJumping
        isJumping = False

        self.images,self.rect = load_sprite_sheet('dino.png',5,1,sizex,sizey,-1)
        self.images1,self.rect1 = load_sprite_sheet('dino_ducking.png',2,1,59,sizey,-1)
        self.rect.bottom = int(0.98*height)
        self.rect.left = width/15
        self.image = self.images[0]
        self.index = 0
        self.counter = 0
        self.score = 0
        self.isDead = False
        self.isDucking = False
        self.isBlinking = False
        self.movement = [0,0]
        self.jumpSpeed = 11.5

        self.stand_pos_width = self.rect.width
        self.duck_pos_width = self.rect1.width

    def draw(self):
        screen.blit(self.image,self.rect)

    def checkbounds(self):
        global isJumping
        if self.rect.bottom > int(0.98*height):
            self.rect.bottom = int(0.98*height)
            isJumping = False

    def update(self):
        global isJumping

        if isJumping:
            self.movement[1] = self.movement[1] + gravity

        if isJumping:
            self.index = 0
        elif self.isBlinking:
            if self.index == 0:
                if self.counter % 400 == 399:
                    self.index = (self.index + 1)%2
            else:
                if self.counter % 20 == 19:
                    self.index = (self.index + 1)%2

        elif self.isDucking:
            if self.counter % 5 == 0:
                self.index = (self.index + 1)%2
        else:
            if self.counter % 5 == 0:
                self.index = (self.index + 1)%2 + 2

        if self.isDead:
           self.index = 4

        if not self.isDucking:
            self.image = self.images[self.index]
            self.rect.width = self.stand_pos_width
        else:
            self.image = self.images1[(self.index)%2]
            self.rect.width = self.duck_pos_width

        self.rect = self.rect.move(self.movement)
        self.checkbounds()

        if not self.isDead and self.counter % 7 == 6 and self.isBlinking == False:
            self.score += 1
            if self.score % 100 == 0 and self.score != 0:
                if pygame.mixer.get_init() != None:
                    checkPoint_sound.play()

        self.counter = (self.counter + 1)

class Cactus(pygame.sprite.Sprite):
    def __init__(self,speed=5,sizex=-1,sizey=-1):
        pygame.sprite.Sprite.__init__(self,self.containers)
        self.images,self.rect = load_sprite_sheet('cacti-small.png',3,1,sizex,sizey,-1)
        self.rect.bottom = int(0.98*height)
        self.rect.left = width + self.rect.width
        self.image = self.images[random.randrange(0,3)]
        self.movement = [-1*speed,0]

        #Nếu không có sa mạc[0] (và vẫn đang cập nhật) được đặt thành cây xương rồng gần nhất
        if desert[0] == None:
            desert[0] = self
        else:
            desert[1] = self

    def draw(self):
        screen.blit(self.image,self.rect)

    def update(self):
        self.rect = self.rect.move(self.movement)



class Ground():
    def __init__(self,speed=-5):
        self.image,self.rect = load_image('ground.png',-1,-1,-1)
        self.image1,self.rect1 = load_image('ground.png',-1,-1,-1)
        self.rect.bottom = height
        self.rect1.bottom = height
        self.rect1.left = self.rect.right
        self.speed = speed

    def draw(self):
        screen.blit(self.image,self.rect)
        screen.blit(self.image1,self.rect1)

    def update(self):
        self.rect.left += self.speed
        self.rect1.left += self.speed

        if self.rect.right < 0:
            self.rect.left = self.rect1.right

        if self.rect1.right < 0:
            self.rect1.left = self.rect.right

class Cloud(pygame.sprite.Sprite):
    def __init__(self,x,y):
        pygame.sprite.Sprite.__init__(self,self.containers)
        self.image,self.rect = load_image('cloud.png',int(90*30/42),30,-1)
        self.speed = 1
        self.rect.left = x
        self.rect.top = y
        self.movement = [-1*self.speed,0]

    def draw(self):
        screen.blit(self.image,self.rect)

    def update(self):
        self.rect = self.rect.move(self.movement)
        if self.rect.right < 0:
            self.kill()

class Scoreboard():
    def __init__(self,x=-1,y=-1):
        self.score = 0
        self.tempimages,self.temprect = load_sprite_sheet('numbers.png',12,1,11,int(11*6/5),-1)
        self.image = pygame.Surface((55,int(11*6/5)))
        self.rect = self.image.get_rect()
        if x == -1:
            self.rect.left = width*0.89
        else:
            self.rect.left = x
        if y == -1:
            self.rect.top = height*0.1
        else:
            self.rect.top = y

    def draw(self):
        screen.blit(self.image,self.rect)

    def update(self,score):

        score_digits = extractDigits(score)
        self.image.fill(background_col)
        for s in score_digits:
            self.image.blit(self.tempimages[s],self.temprect)
            self.temprect.left += self.temprect.width
        self.temprect.left = 0


def introscreen():
    global isJumping
    temp_dino = Dino(44,47)
    temp_dino.isBlinking = True
    gameStart = False

    temp_ground,temp_ground_rect = load_sprite_sheet('ground.png',15,1,-1,-1,-1)
    temp_ground_rect.left = width/20
    temp_ground_rect.bottom = height

    logo,logo_rect = load_image('logo.png',300,140,-1)
    logo_rect.centerx = width*0.6
    logo_rect.centery = height*0.6
    while not gameStart:
        if pygame.display.get_surface() == None:
            print("Couldn't load display surface")
            return True
        else:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                        isJumping = True
                        temp_dino.isBlinking = False
                        temp_dino.movement[1] = -1*temp_dino.jumpSpeed

        temp_dino.update()

        if pygame.display.get_surface() != None:
            screen.fill(background_col)
            screen.blit(temp_ground[0],temp_ground_rect)
            if temp_dino.isBlinking:
                screen.blit(logo,logo_rect)
            temp_dino.draw()

            pygame.display.update()

        clock.tick(FPS)
        if isJumping == False and temp_dino.isBlinking == False:
            gameStart = True

# ==================================================================================================
def gameplay():
  #Initalizing vars toàn cầu trong trò chơi
    global desert
    global distance
    global action
    global lastRun
    global high_score
    global isJumping


    gamespeed = 4
    startMenu = False
    gameOver = False
    gameQuit = False
    playerDino = Dino(44,47)
    new_ground = Ground(-1*gamespeed)
    scb = Scoreboard()
    highsc = Scoreboard(width*0.78)
    counter = 0

    cacti = pygame.sprite.Group()
    clouds = pygame.sprite.Group()
    last_obstacle = pygame.sprite.Group()

    Cactus.containers = cacti
    Cloud.containers = clouds

    retbutton_image,retbutton_rect = load_image('replay_button.png',35,31,-1)
    gameover_image,gameover_rect = load_image('game_over.png',190,11,-1)

    temp_images,temp_rect = load_sprite_sheet('numbers.png',12,1,11,int(11*6/5),-1)
    HI_image = pygame.Surface((22,int(11*6/5)))
    HI_rect = HI_image.get_rect()
    HI_image.fill(background_col)
    HI_image.blit(temp_images[10],temp_rect)
    temp_rect.left += temp_rect.width
    HI_image.blit(temp_images[11],temp_rect)
    HI_rect.top = height*0.1
    HI_rect.left = width*0.73



    while not gameQuit:
        while startMenu:
            pass
        while not gameOver:
            if pygame.display.get_surface() == None:
                print("Couldn't load display surface")
                gameQuit = True
                gameOver = True
            else:
                #Cách chức năng dự đoán (dựa trên hành động) ảnh hưởng đến bước nhảy của khủng long
                if action == 1:
                    if playerDino.rect.bottom == int(0.98*height):
                        isJumping = True
                        if pygame.mixer.get_init() != None:
                            jump_sound.play()
                        playerDino.movement[1] = -1*playerDino.jumpSpeed

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        gameQuit = True
                        gameOver = True

                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE: #đã thêm getJump để chuyển boolean từ tác nhân
                            if playerDino.rect.bottom == int(0.98*height):
                                isJumping = True
                                if pygame.mixer.get_init() != None:
                                    jump_sound.play()
                                playerDino.movement[1] = -1*playerDino.jumpSpeed

                        if event.key == pygame.K_DOWN:
                            if not (isJumping and playerDino.isDead):
                                playerDino.isDucking = True

                    if event.type == pygame.KEYUP:
                        if event.key == pygame.K_DOWN:
                            playerDino.isDucking = False
            for c in cacti:
                c.movement[0] = -1*gamespeed
                if pygame.sprite.collide_mask(playerDino,c):
                    playerDino.isDead = True
                    if pygame.mixer.get_init() != None:
                        die_sound.play()

            if len(cacti) < 2:
                if len(cacti) == 0:
                    last_obstacle.empty()
                    last_obstacle.add(Cactus(gamespeed,40,40))
                else:
                    for l in last_obstacle:
                        if l.rect.right < width*0.7 and random.randrange(0,50) == 10:
                            last_obstacle.empty()
                            last_obstacle.add(Cactus(gamespeed, 40, 40))

            if len(clouds) < 5 and random.randrange(0,300) == 10:
                Cloud(width,new_func())

          #Nếu có một cây xương rồng, hãy tính khoảng cách
            if desert[0] != None:
                distance = desert[0].rect.left - playerDino.rect.right

          #For để kiểm tra xem tại bất kỳ một trong các "điểm nhảy" nào, nếu có, hãy hỏi chức năng "hành động"
            if desert[0] != None:
                for i in range(0, POINT_DISTANCE*NUM_POINTS, POINT_DISTANCE):
                    if distance == i:
                        #bprint("Đang bắt một hành động tại vị trí: " + str(i))
                        action = act(i//POINT_DISTANCE)
                        lastRun[i//POINT_DISTANCE] = action

            playerDino.update()
            cacti.update()
            clouds.update()
            new_ground.update()

          #Nếu hitbox xương rồng vượt qua hitbox khủng long
            if desert[0].rect.right < playerDino.rect.left and not playerDino.isDead:
                desert[0].kill() #Xóa đối tượng cây xương rồng (nó không thể đánh khủng long nữa)
                desert[0] = desert[1] #Xóa khỏi sa mạc[]
                remember(False) #Pass Sai cho "Không chết!" ghi nhớ chức năng

            scb.update(playerDino.score)
            highsc.update(high_score)

            if pygame.display.get_surface() != None:
                screen.fill(background_col)
                new_ground.draw()
                clouds.draw(screen)
                scb.draw()
                if high_score != 0:
                    highsc.draw()
                    screen.blit(HI_image,HI_rect)
                cacti.draw(screen)
                playerDino.draw()

                pygame.display.update()
            clock.tick(FPS)

            if playerDino.isDead:
                gameOver = True
                if playerDino.score > high_score:
                    high_score = playerDino.score

            #Thay đổi gia tốc của trò chơi thành 0 thay vì 1
            if counter%700 == 699:
                new_ground.speed -= 0
                gamespeed += 0

            counter = (counter + 1)

        if gameQuit:
            break

        while gameOver:
            # Tự động khởi động lại trò chơi nếu đúng
            if restart:
                remember(True) ## Truyền true cho "Died" cho chức năng ghi nhớ
                gameOver = False
                action = 0#Reintialize hành động và sa mạc cho trò chơi mới
                desert = [None, None]
                gameplay()

            if pygame.display.get_surface() == None:
                print("Couldn't load display surface")
                gameQuit = True
                gameOver = False
            else:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        gameQuit = True
                        gameOver = False
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            gameQuit = True
                            gameOver = False
                        gameplay()

                        if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE: #added getJump to pass booleans from agent
                            gameOver = False
                            action = 0
                            desert = [None,None]
                            gameplay()
            highsc.update(high_score)
            if pygame.display.get_surface() != None:
                disp_gameOver_msg(retbutton_image,gameover_image)
                if high_score != 0:
                    highsc.draw()
                    screen.blit(HI_image,HI_rect)
                pygame.display.update()
            clock.tick(FPS)

    pygame.quit()
    quit()

import random

def new_func():
    return random.randrange(int(height/5), int(height/2))



#Tất cả các phương pháp ngoài thời điểm này là mã của chúng tôi

# Chức năng này chạy khi tác nhân vượt qua cây xương rồng hoặc chết
# Mục đích của nó là nhớ lại những hành động nó đã thực hiện trong lần chạy trước và thêm
# trọng số mới cho mảng jumpMemory và noJumpMemory
def remember(isDead):
    global lastRun
    global jumpMemory
    global e
    global noJumpMemory
    global iteration

  #Increase iterationa và in ra bàn điều khiển
    iteration += 1
    print("Iteration " + str(iteration))

   #Reduce e cho đến khi đạt eGoal
    if e > eGoal:
        e -= eDecay

    #Trọng số của một lần lặp không thành công
    if isDead:
        print("DIED!")
        for i in range(0, NUM_POINTS):
            if lastRun[i] == 0:
                noJumpMemory[i] -= 1

            if lastRun[i] == 1:
                jumpMemory[i] -= 5

# Trọng số cho một lần lặp thành công
    else:
        print("SUCCESS!")
        for i in range(0, NUM_POINTS):
            if lastRun[i] == 0:
                noJumpMemory[i] += .25
            else:
                jumpMemory[i] += 5

 # Theo dõi giá trị điện tử trong bảng điều khiển
    print("Epsilon: " + str(e))
    for x in range(0, NUM_POINTS):
        print("Jump: " + str(jumpMemory[x])+ " NoJump: " + str(noJumpMemory[x]))


#Đây là cái được gọi khi chúng tôi muốn AI hành động, nơi nó hành động được xác định bởi NUM_POINTS và POINT_DISTANCE
#Nó chọn giữa khám phá và dự đoán thông qua tạo số ngẫu nhiên
def act(state):
    global action
    global lastRun

    randomNum = random.random()

    if randomNum < e:
        if isJumping:
            action = 0
            #print("Forced to guess 0 at space " + str(state * POINT_DISTANCE) + " ... " + str(distance))
        else:
            if state < (NUM_POINTS)/2: #If at area between halfway and Cactus
                action = random.randint(0,1)
            else:

                if randomNum < SPREAD_PERCENT:
                    action = 1
                else:
                    action = 0


            #action = random.randint(0,1)
            #print("Guessing " + str(action) + " at space " + str(state*POINT_DISTANCE)+ " ... " + str(distance))

        #print("Guessing " + str(action) + " at space " + str(state) + " at distance " + str(distance))
    else:

        action = predict(state)
        #print("Predicting " + str(action) + " at space " + str(state*POINT_DISTANCE)+ " ... " + str(distance))

    lastRun[state] = action
    return action

#Điều này được gọi khi AI muốn dự đoán. Nó so sánh trọng lượng tại vị trí này
#Và lấy biểu đồ có trọng số cao hơn. Nếu bằng nhau thì hành động ngẫu nhiên
def predict(state):
    global intentions

    if jumpMemory[state] > noJumpMemory[state] and not isJumping:
        #print("Will jump")
        act = 1

    elif jumpMemory[state] == noJumpMemory[state]:
        if isJumping:
            act = 0
        else:
            act = random.randint(0,1)
        #print("Could do either")

        #print("Me Guess: " + str(act))
    elif jumpMemory[state] > noJumpMemory[state] and isJumping:
        #print("Cant jump")
        act = 0

    else:
        #print("Shouldnt jump")
        act = 0

    return act


def save_weights():
    with h5py.File('luu_thong_so_jump_nojump.h5', 'w') as file:
        file.create_dataset('jump_memory', data=jumpMemory)
        file.create_dataset('no_jump_memory', data=noJumpMemory)

def main():
    isGameQuit = introscreen()
    if not isGameQuit:
        gameplay()
        save_weights()

main()
