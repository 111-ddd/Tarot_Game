import json
import os
import random
import time
import sys

import pygame as pg
from pygame.locals import *

# 初始化
pg.init()
pg.mixer.init()
clock = pg.time.Clock()

# 窗口属性
ww = 1366
wh = 768
fr = ww / 1366
card_size = (133, 230)

# 配置读取
with open('Tarot_config.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    music_vol = data['setting']['背景音量']
    sound_vol = data['setting']['音效音量']

# 身份牌列表
identity = data['identity']

# 读取皮肤
skin = data['skin']

# 猜拳
player_chosed = None
Bot_result = None
gf_res = ['胜利', '平局', '失败']


def g_rect(objects):
    return pg.Rect(objects.x, objects.y, objects.width, objects.height)


def finger_guess(result1, result2):
    if ((result1 == 0 and result2 == 1) or
            (result1 == 1 and result2 == 2) or
            (result1 == 2 and result2 == 0)):
        return 0
    elif result1 == result2:
        return 1
    else:
        return 2


def save_config(data_n):
    with open('Tarot_config.json', 'w', encoding='utf-8') as config:
        json.dump(data_n, config, ensure_ascii=False, indent=4)


def read_directory(directory_name, objects):
    for filename in os.listdir(r"./" + directory_name):
        directory = directory_name + '/' + filename
        if '.' not in filename:
            read_directory(directory, objects)
            continue
        objects[filename] = pg.image.load(directory)


def transform_scale(image, width, height):
    return pg.transform.smoothscale(image, (width, height))


def wash_cards(wait_card):
    wait_wash = list(set(wait_card) - set(cards['弃牌堆']))
    random.shuffle(wait_wash)
    if wait_card == cards['大阿卡纳']:
        for washing in wait_wash:
            washing.is_on = random.choice([True, False])
    return wait_wash


# 载入图片
base_directory = 'Tarot_resource/'
bili_skin = base_directory + 'Card/BiliBli'
rider_skin = base_directory + 'Card/Rider'
UI = base_directory + 'UI'

img_ui, img_bili, img_rider = {}, {}, {}
img_directory = [bili_skin, rider_skin, UI]
img_list = [img_bili, img_rider, img_ui]
for i in range(0, 3):
    read_directory(img_directory[i], img_list[i])

# 载入字体
font_direvtory = 'Tarot_resource/Font/'

# 载入音乐
music_directory = 'Tarot_resource/Music'
pg.mixer.music.load(music_directory + '/CalabiYau/' + '内心的炽热.mp3')
pg.mixer.music.set_volume(0)
pg.mixer.music.play(-1)
pg.mixer.music.pause()
pg.mixer.music.set_volume(music_vol)

# 载入音效
sound_directory = music_directory + '/Sound/'
touch_card_s = pg.mixer.Sound(sound_directory + '碰牌.mp3')
button_sd = pg.mixer.Sound(sound_directory + '按钮.wav')
touch_card_s.set_volume(sound_vol)
button_sd.set_volume(sound_vol)


class Text:
    def __init__(self, font_size, text, t_x, t_y, font='黑体.ttf', color=(255, 255, 255)):
        self.font = font
        self.x = t_x
        self.y = t_y
        self.font_size = font_size
        self.text = text
        self.color = color

    def draw(self):
        ob = pg.font.Font(font_direvtory + self.font, self.font_size)
        render = ob.render(self.text, True, self.color)
        rect = render.get_rect()
        rect.center = (self.x, self.y)
        screen.blit(render, rect)


class Player:
    def __init__(self, name, identity_chosen=False, can_get=False,
                 identity_card=None, is_active=False,
                 hand_cards=None, points=0, hand_card_pos=None, get_card=False,
                 is_first=False, turn_complete=False, gg=False, skill_complete=False,
                 decide_complete=True
                 ):
        if hand_cards is None:
            hand_cards = []
        if hand_card_pos is None:
            hand_card_pos = [ww * 0.02, wh * 0.7]
        self.hand_cards = hand_cards
        self.gg = gg
        self.can_get = can_get
        self.turn_complete = turn_complete
        self.decide_complete = decide_complete
        self.skill_complete = skill_complete
        self.is_first = is_first
        self.name = name
        self.get_card = get_card
        self.hand_card_pos = hand_card_pos
        self.identity_chosen = identity_chosen
        self.is_active = is_active
        self.identity_card = identity_card
        self.hand_cards = hand_cards
        self.points = points

    def get_cards(self, chose_cards, chose_type):
        for c in chose_cards:
            if c.card_types == chose_type and not c in cards['弃牌堆']:
                rect = g_rect(c)
                if self.name == 'Bot' or rect.collidepoint(pg.mouse.get_pos()):
                    touch_card_s.play()
                    self.hand_cards.append(c)
                    cards['弃牌堆'].append(c)
                    print(self.name + '抽取了' + str(c.is_on) + '的' + c.card_id)
                    break


class Button:
    NORMAL = 0
    ON = 1
    DOWN = 2

    def __init__(self, img_n, width, height, b_x, b_y,
                 text, font='黑体.ttf', font_size=int(40 * fr), f_color=(255, 255, 255),
                 img_on=None, img_down=None, status=0):
        self.imgs = []
        self.imgs.append(img_n)
        self.imgs.append(img_on)
        self.imgs.append(img_down)
        for img_num in range(0, 3):
            if self.imgs[img_num] is not None:
                self.imgs[img_num] = transform_scale(self.imgs[img_num], width, height)
            else:
                self.imgs[img_num] = transform_scale(self.imgs[img_num - 1], width, height)
        self.status = status
        self.x = b_x
        self.y = b_y
        self.width = width
        self.height = height
        self.text = text
        self.font = font
        self.f_color = f_color
        self.font_size = font_size

    def draw(self):
        font_ob = pg.font.Font('Tarot_resource/Font/{}'.format(self.font), int(self.font_size))
        text_surf = font_ob.render(self.text, True, self.f_color)

        # 文字坐标
        fx = (self.width / 2) - (text_surf.get_width() / 2)
        fy = (self.height / 2) - (text_surf.get_height() / 2.5)

        # 绘制按钮
        if self.imgs[self.status]:
            b_img = transform_scale(self.imgs[self.status], self.width, self.height)
            screen.blit(b_img, (self.x, self.y))

        # 绘制文字
        screen.blit(text_surf, (self.x + fx, self.y + fy))

    def check_status(self):
        rect = g_rect(self)
        # 检测状态
        if rect.collidepoint(pg.mouse.get_pos()):
            if event.type == MOUSEMOTION:
                if self.status != Button.DOWN:
                    self.status = Button.ON
            elif event.type == MOUSEBUTTONUP:
                self.status = Button.NORMAL
            elif event.type == MOUSEBUTTONDOWN:
                self.status = Button.DOWN
        else:
            self.status = Button.NORMAL


class SettingBar(Button):
    def __init__(self, width, height, bar_x, bar_y, text, rate):
        super().__init__(img_ui['滑动条.png'], width, height, bar_x, bar_y, text)
        self.rate = rate

    def draw(self):
        slide_bar = transform_scale(img_ui['滑动条.png'], self.width, self.height)
        slide_block = transform_scale(img_ui['滑动块.png'], self.width * 0.016, self.height * 0.78)

        font_size = int(40 * fr)
        bar_h = self.y + slide_bar.height * 0.5
        bar_text = Text(font_size, self.text, self.x + slide_bar.width * 0.07,
                        bar_h)
        bar_rate = Text(font_size, '{}%'.format(int(self.rate * 100)), self.x + slide_bar.width * 0.96,
                        bar_h)
        screen.blit(slide_bar, (self.x, self.y))
        # 滑动条的轨道长度0.67 - 0.91
        screen.blit(slide_block,
                    (self.x + slide_bar.width * (0.67 + self.rate * 0.24),
                     self.y + slide_bar.height * 0.1))
        bar_text.draw()
        bar_rate.draw()


class Card(Button):
    def __init__(self, card_id, card_types, front, points, can_turn=True, is_used=False,
                 effct_ban=False, point_ban=False, is_open=False, is_protected=False,
                 c_x=0, c_y=0, c_width=card_size[0], c_height=card_size[1], is_on=True,
                 is_tower = False):
        super().__init__(front, c_width, c_height, c_x, c_y, None, img_down=front)
        self.card_id = card_id
        self.points = points
        self.can_turn = can_turn
        self.is_on = is_on
        self.is_used = is_used
        self.card_types = card_types
        self.effct_ban = effct_ban
        self.point_ban = point_ban
        self.is_open = is_open
        self.is_protected = is_protected
        self.is_tower = is_tower

    def turn_on_card(self, status):
        rect = g_rect(self)
        if status == 'on':
            turned = True
        elif status == 'off':
            turned = False
        else:
            turned = not self.is_open

        if rect.collidepoint(pg.mouse.get_pos()):
            if (event.type == MOUSEBUTTONUP and
                    self.can_turn and self.is_open == (not turned)):
                self.is_open = turned
                return self
        else:
            return False

    def draw(self):
        # 判断是否翻开
        if self.is_open:
            img_show = self.imgs[0]
            # 判断正逆位
            if not self.is_on:
                img_show = pg.transform.rotate(img_show, 180)
        else:
            img_show = cards['back'][0].imgs[0]
        screen.blit(transform_scale(img_show, self.width, self.height), (self.x, self.y))

        # 绘制状态
        ban_img_s = self.width * 0.22
        tag_x = self.x + self.width - ban_img_s - self.width * 0.02
        tag_y = self.y + self.height * 0.02
        p_img_width, p_img_height = self.width * 0.22, self.height * 0.165

        if self.point_ban:
            ban_img = transform_scale(img_ui['禁点.png'], ban_img_s, ban_img_s)
            screen.blit(ban_img, (tag_x, tag_y))
            tag_x -= ban_img_s + self.width * 0.03

        if self.effct_ban:
            ban_img = transform_scale(img_ui['禁效.png'], ban_img_s, ban_img_s)
            screen.blit(ban_img, (tag_x, tag_y))
            tag_x -= ban_img_s + self.width * 0.03

        if self.is_protected:
            protect_img = transform_scale(img_ui['保护.png'], ban_img_s, ban_img_s)
            screen.blit(protect_img, (tag_x, tag_y))
            tag_x -= ban_img_s + self.width * 0.03

        if self.is_tower:
            tower_img = transform_scale(img_ui['塔.png'], ban_img_s, ban_img_s)
            screen.blit(tower_img, (tag_x, tag_y))
            tag_x -= ban_img_s + self.width * 0.03

    def clean_card(self):
        self.can_turn = True
        self.is_used = False
        self.effct_ban = False
        self.point_ban = False
        self.is_open = False
        self.is_protected = False
        self.is_tower = False

# 创建开局计时器
start_game = None

# 创建卡牌
card_type = ['ace', '大阿卡纳', '小阿卡纳', 'back']
card_skin = []

small_akanas = []
big_akanas = []
ace = []
back = []
fw_card = []

cards = {'ace': ace, '大阿卡纳': big_akanas,
         '小阿卡纳': small_akanas,
         'back': back,
         '弃牌堆': fw_card}

for i in ['ace', 'big', 'small', 'back']:
    if skin[i] == 'bili':
        card_skin.append(bili_skin)
    elif skin[i] == 'rider':
        card_skin.append(rider_skin)
    else:
        card_skin.append(rider_skin)

for i in range(0, 3):
    if card_skin[i] == bili_skin:
        img_load = img_bili
    elif card_skin[i] == rider_skin:
        img_load = img_rider
    else:
        img_load = img_rider

    for j in os.listdir(card_skin[i] + '/{}'.format(card_type[i])):
        point = j[0:2]
        cards[card_type[i]].append(Card('{}'.format(j), card_type[i],
                                        img_load['{}'.format(j)], point))

# 加载卡片背面
back_img = img_rider
if skin['back'] == 'bili':
    back_img = img_bili
elif skin['back'] == 'rider':
    back_img = img_rider

cards['back'].append(Card('Back.png', 'back', back_img['Back.png'], 0))

# 删除小阿卡纳中的身份牌
delete_list = []
for i in cards['小阿卡纳']:
    for j in identity:
        if i.card_id == '{}.png'.format(j):
            i.card_types = '身份牌'
            cards['ace'].append(i)
            delete_list.append(i)

for i in delete_list:
    cards['小阿卡纳'].remove(i)

# 洗牌
for i in cards.keys():
    random.shuffle(cards[i])

# 创建玩家对象
Bot = Player('Bot')
Player_T = Player('Edwad_过客')
names = [Bot, Player_T]

# 选人界面标题文字
title_chose_color = (160, 31, 235)
chose_title = Text(80, '请抽取身份牌', ww * 0.51, wh * 0.25, color=title_chose_color)
chose_title2 = Text(80, '', ww * 0.51, wh * 0.25, color=title_chose_color)

# 建立状态量
gui = 'home'
active_card = None
slide_bars_active = {}
start_gf = False
chosed_card = None
chosed_card_m = None
game_winner = None
seeing = None
gf_winner = None
for i in data['setting'].keys():
    slide_bars_active[SettingBar(ww * 0.9151, wh * 0.0781, ww * 0.0439,
                                 wh * 0.2083, i, data['setting'][i])] = False

# 信息栏提示
messages = '轮到你抽取手牌'


def sound_icon(switch):
    if switch:
        sound_bg.status = 0
        pg.mixer.music.unpause()
    else:
        sound_bg.status = 2
        pg.mixer.music.pause()


def guess_finger_ui():
    B_size = ww * 0.1
    B_pos = [ww * 0.235, wh * 0.45]
    buttons_name = ['石头', '剪刀', '布']
    buttons = []
    over_gf = time.time()
    player_chosed = None
    Bot_result = None

    # 绘制背景板
    base_bg = transform_scale(img_ui['方块按钮1.png'], ww * 0.465, wh * 0.35)
    screen.blit(base_bg, (ww * 0.18, wh * 0.33))

    # 绘制文字提示
    gf_tip = Text(int(fr * 40), '请选择你的手势', ww * 0.425, wh * 0.39)

    for gf in range(0, 3):
        buttons.append(Button(img_ui['{}.png'.format(buttons_name[gf])],
                              B_size, B_size, B_pos[0], B_pos[1], ''))
        buttons[gf].draw()
        B_pos[0] += ww * 0.13

    for player_chose in range(0, 3):
        if event.type == MOUSEBUTTONUP:
            rect = g_rect(buttons[player_chose])
            if rect.collidepoint(event.pos):
                Bot_result = random.choice([0, 1, 2])
                player_chosed = player_chose

    if player_chosed:
        fg_result = finger_guess(player_chosed, Bot_result)
        gf_tip.text = ('你选择了' + buttons_name[player_chosed]
                       + '对方选择了' + buttons_name[Bot_result]
                       + '结果:' + gf_res[fg_result])
        if time.time() - over_gf >= 3:
            if fg_result != 1:
                return finger_guess(player_chosed, Bot_result)
            else:
                return guess_finger_ui(Bot_result)
        else:
            pass

    gf_tip.draw()


'''--------------------------
           主页UI
--------------------------'''
# 基本UI
bg = transform_scale(img_ui['bg1.jpg'], ww, wh)
title = transform_scale(img_ui['标题.png'], ww * 0.6442, wh * 0.1861)
if data['music_switch']:
    bg_sound_status = 0
else:
    bg_sound_status = 2
sound_bg = Button(img_ui['音量_开.png'], ww * 0.0586, wh * 0.1041, ww * 0.9297, wh * 0.8789,
                  '', img_down=img_ui['音量_关.png'], status=bg_sound_status)
sound_icon(data['music_switch'])

# 按钮属性
button_x = ww * 0.2928
button_y = wh * 0.3776
button_width = ww * 0.4319
button_height = wh * 0.138
button_text = ['单人模式', '多人模式', '设置']
button_home = []
for i in range(0, 3):
    button_home.append(Button(img_ui['首页大按钮.png'], button_width, button_height,
                              button_x, button_y, button_text[i], font_size=int(50 * fr),
                              img_on=img_ui['首页大按钮1.png'], img_down=img_ui['首页大按钮2.png']))
    button_y += wh * 0.1693

'''--------------------------
           设置UI
--------------------------'''
# 按钮
save_cg = Button(img_ui['方块按钮.png'], ww * 0.1245, wh * 0.0911, ww * 0.8419, wh * 0.8724, '确定',
                 img_on=img_ui['方块按钮1.png'], img_down=img_ui['方块按钮2.png'])

for i in range(0, len(data['setting'])):
    list(slide_bars_active.keys())[i] = SettingBar(ww * 0.9151, wh * 0.0781, ww * 0.0439,
                                                   wh * 0.2083, list(data['setting'].keys())[i],
                                                   list(data['setting'].values())[i])

'''--------------------------
           结算UI
--------------------------'''
# 按钮
go_back_b = Button(img_ui['方块按钮.png'], ww * 0.15, wh * 0.01,
                   ww * 0.54, wh * 0.82, '返回', img_down=img_ui['方块按钮2.png'],
                   img_on=img_ui['方块按钮1.png'])

'''--------------------------
           战斗UI
--------------------------'''
# 按钮
see_ok = Button(img_ui['方块按钮.png'], ww * 0.1245, wh * 0.0911, ww * 0.4, wh * 0.49, '看完了',
                 img_on=img_ui['方块按钮1.png'], img_down=img_ui['方块按钮2.png'])

# 创建窗口
screen = pg.display.set_mode((ww, wh), flags=RESIZABLE)
pg.display.set_caption("塔罗对战 by Edwad_过客")

while True:
    clock.tick(60)

    # 捕捉窗口变化
    win_size = pg.display.get_surface().get_size()
    ww = win_size[0]
    wh = win_size[1]

    # 刷新背景图片信息
    bg = transform_scale(img_ui['bg1.jpg'], ww, wh)

    # 调整字体大小
    fr = ww / 1366

    # 刷新音量大小
    pg.mixer.music.set_volume(data['setting']['背景音量'])
    touch_card_s.set_volume(data['setting']['音效音量'])
    button_sd.set_volume(data['setting']['音效音量'])

    # 绘制基础UI
    if gui == 'home':
        # 背景
        # 基本UI
        title = transform_scale(img_ui['标题.png'], ww * 0.6442, wh * 0.1861)
        screen.blit(bg, (0, 0))
        screen.blit(title, (ww * 0.1867, wh * 0.0586))

        # 音量按钮
        sound_bg.width, sound_bg.height, sound_bg.x, sound_bg.y = (
            ww * 0.0586, wh * 0.1041, ww * 0.9297, wh * 0.8789,)
        sound_bg.draw()

        # 绘制按钮
        button_x = ww * 0.2928
        button_y = wh * 0.3776
        button_width = ww * 0.4319
        button_height = wh * 0.138
        for i in button_home:
            i.width, i.height, i.x, i.y = button_width, button_height, button_x, button_y
            i.font_size = int(50 * fr)
            i.draw()
            button_y += wh * 0.1693

    elif gui == 'setting':
        # 基本UI
        bg_setting = transform_scale(img_ui['bg2.jpeg'], ww, wh)
        setting_title = transform_scale(img_ui['设置标题.png'], ww * 0.2225, wh * 0.1419)

        screen.blit(bg_setting, (0, 0))
        screen.blit(setting_title, (0, wh * 0.0391))

        for i in range(0,len(data['setting'])):
            setting_bar_ob = list(slide_bars_active.keys())[i]
            setting_bar_ob.width, setting_bar_ob.height, setting_bar_ob.x, setting_bar_ob.y = \
                (ww * 0.9151, wh * 0.0781, ww * 0.0439,
                 wh * 0.2083 + i * (wh * 0.0781 + wh * 0.018))
            setting_bar_ob.draw()

        # 按钮
        save_cg.width, save_cg.height, save_cg.x, save_cg.y = (
            ww * 0.1245, wh * 0.0911, ww * 0.8419, wh * 0.8724)
        save_cg.font_size = int(fr * 40)
        save_cg.draw()

    elif gui == 'fighting':
        bg_right = transform_scale(img_ui['信息栏.png'], ww * 0.1537, wh)

        screen.blit(bg, (0, 0))
        screen.blit(bg_right, (ww * 0.847, 0))

        # 调整卡片大小
        card_size = (ww * 0.0974, wh * 0.2994)
        for i in cards.keys():
            for j in cards[i]:
                j.width = card_size[0]
                j.height = card_size[1]

        # 检测是否为单人模式
        if Bot.name == 'Bot':
            # 检测对手是否选择身份牌
            if not Bot.identity_chosen:
                # 机器人选身份
                num = random.randint(0, len(cards['ace']) - 1)
                if cards['ace'][num] not in cards['弃牌堆']:
                    Bot.identity_card = cards['ace'][num]
                    Bot.identity_card.is_open = True
                    Bot.identity_chosen = True
                    cards['弃牌堆'].append(Bot.identity_card)
            else:
                # 绘制信息栏
                x, y = ww * 0.8748, wh * 0.0260
                for i in [Bot, Player_T]:
                    i.identity_card.x, i.identity_card.y = x, y
                    i.identity_card.draw()
                    y += wh * 0.5013

                id_pos = [ww * 0.9224, wh * 0.3607]
                y_differ = wh * 0.4313
                for i in names:
                    # 绘制用户名称
                    text_id = Text(int(35 * fr), i.name, id_pos[0], id_pos[1])
                    text_id.draw()
                    id_pos[1] += wh * 0.07

                    # 计算点数
                    i.points = 0
                    for opened_cards in i.hand_cards:
                        if opened_cards.is_open:
                            if opened_cards.point_ban:
                                i.points += 0
                            else:
                                card_p = int(opened_cards.points)
                                if opened_cards.is_tower:
                                    if card_p >= 10:
                                        card_p = int(str(card_p)[1:])
                                    else:
                                        card_p = 0

                                if opened_cards.is_on:
                                    i.points += card_p
                                else:
                                    i.points -= card_p

                    # 绘制分数板
                    text_points = Text(int(45 * fr), str(i.points), id_pos[0], id_pos[1],
                                       font = 'Minecraft.otf')
                    text_points.draw()
                    id_pos[1] += y_differ

                    # 绘制手牌
                    cards_interval = ww * 0.103
                    for a in names:
                        if a == Bot:
                            a.hand_card_pos = [ww * 0.736, wh * 0.02]
                        else:
                            a.hand_card_pos = [ww * 0.014, wh * 0.69]

                        for j in a.hand_cards:
                            j.x, j.y = a.hand_card_pos[0], a.hand_card_pos[1]
                            j.draw()

                            if a == Bot and a.hand_card_pos[0] <= ww * 0.016:
                                a.hand_card_pos = [ww * 0.736, wh * 0.02 * 2 + card_size[1]]
                            elif a != Bot and a.hand_card_pos[0] >= ww * 0.733:
                                a.hand_card_pos = [ww * 0.014, wh * 0.67 - card_size[1]]
                            else:
                                if a == Bot:
                                    a.hand_card_pos[0] -= cards_interval
                                else:
                                    a.hand_card_pos[0] += cards_interval

                # 绘制牌堆
                cards_hill = ['小阿卡纳', '大阿卡纳']
                cards_hill_pos = [ww * 0.323, wh * 0.355]
                for i in cards_hill:
                    for j in list(set(cards[i]) - set(cards['弃牌堆'])):
                        j.x = cards_hill_pos[0]
                        j.y = cards_hill_pos[1]
                        j.draw()
                    cards_hill_pos[0] += ww * 0.105

                # 绘制消息提示栏
                text_message = Text(int(25 * fr), messages, ww * 0.923, wh * 0.49, color=(255, 0, 0))
                text_message.draw()

                # 机器人拿手牌
                if Player_T.get_card:
                    messages = '轮到对方抽牌'
                    if not Bot.get_card:
                        if len(Bot.hand_cards) < data['cards_min']:
                            if time.time() - start_game > 0.5:
                                washed_cards = wash_cards(cards['大阿卡纳'])
                                Bot.get_cards(washed_cards, '大阿卡纳')
                                start_game = time.time()
                        else:
                            Bot.get_card = True
                    else:
                        # 双方都拿完手牌

                        # 如果没有先手
                        if not Bot.is_first and not Player_T.is_first:
                            messages = '猜拳定先手'
                            Bot_hand = random.choice([0, 1, 2])
                            if gf_winner == None:
                                B_size = ww * 0.1
                                B_pos = [ww * 0.235, wh * 0.45]
                                buttons_name = ['石头', '剪刀', '布']
                                buttons = []

                                # 绘制背景板
                                base_bg = transform_scale(img_ui['方块按钮1.png'], ww * 0.465, wh * 0.35)
                                screen.blit(base_bg, (ww * 0.18, wh * 0.33))

                                # 绘制文字提示
                                gf_tip = Text(int(fr * 40), '请选择你的手势', ww * 0.425, wh * 0.39)

                                # 绘制按钮
                                for gf in range(0, 3):
                                    buttons.append(Button(img_ui['{}.png'.format(buttons_name[gf])],
                                                          B_size, B_size, B_pos[0], B_pos[1], ''))
                                    buttons[gf].draw()
                                    B_pos[0] += ww * 0.13

                                if player_chosed != None:
                                    fg_result = finger_guess(player_chosed, Bot_result)
                                    gf_tip.text = ('你:' + buttons_name[player_chosed]
                                                   + ' 对方:' + buttons_name[Bot_result]
                                                   + ' ' + gf_res[fg_result])

                                    if fg_result != 1:
                                        if time.time() - over_gf >= 3:
                                            gf_winner = fg_result
                                        start_gf = False
                                    else:
                                        start_gf = True
                                else:
                                    start_gf = True

                                gf_tip.draw()
                            else:
                                # 猜拳完毕
                                if gf_winner == 2:
                                    Bot.is_first = True
                                    Bot.is_active = True
                                else:
                                    Player_T.is_active = True
                                    Player_T.is_first = True
                        else:
                            # 判断游戏是否结束
                            if (names[0].gg and names[1].gg) or game_winner:
                                if time.time() - over_game >= data['over_game']:
                                    gui = 'overgame'
                                else:
                                    messages = ('{}秒后转到结算'
                                                .format(int(data['over_game'] - (time.time() - over_game))))
                            else:
                                # 决定先后手完成
                                for i in names:
                                    # 更改行动状态
                                    if i.is_active and not i.gg:
                                        # 更改提示
                                        if i == Bot:
                                            messages = '敌方行动回合'
                                        else:
                                            messages = '你的行动回合'

                                        if i.decide_complete:
                                            # 判定完成
                                            if i.turn_complete:
                                                # 判定完毕并且翻完牌后执行
                                                if i.skill_complete:
                                                    # 判定完毕翻完牌并且技能释放结束
                                                    i.is_active = False
                                                    i.turn_complete = False
                                                    i.skill_complete = False
                                                    # 将另一个行动回合开启,关闭当前行动回合
                                                    for j in names:
                                                        if j != i:
                                                            j.is_active = True

                                                    # 手牌状态更新
                                                    active_card.is_used = True

                                                    # 计算未翻开手牌数量
                                                    no_use = len(i.hand_cards)
                                                    for no_used in i.hand_cards:
                                                        if no_used.is_used:
                                                            no_use -= 1

                                                    if no_use == 0:
                                                        i.is_active = False
                                                        i.gg = True
                                                        print(i.name + '结束了')
                                                        for j in names:
                                                            if j != i:
                                                                j.is_active = True
                                                        over_game = time.time()
                                                    else:
                                                        i.gg = False

                                                elif (active_card and
                                                      i.skill_complete == False and
                                                      active_card.effct_ban == False):
                                                    # 判定完毕翻完牌但技能释放中
                                                    if active_card.is_used == False:
                                                        for ey in names:
                                                            if ey != i:
                                                                enemy = ey
                                                        c_name = active_card.card_id[0:2]

                                                        # 愚者即赢
                                                        if c_name == '00':
                                                            if active_card.is_on:
                                                                game_winner = i
                                                            else:
                                                                game_winner = enemy
                                                            over_game = time.time()
                                                            i.skill_complete = True

                                                        # 魔术师拿别人一张牌(任意)
                                                        elif c_name == '01':
                                                            if (i == Bot and active_card.is_on or
                                                                    i == Player_T and not active_card.is_on):
                                                                messages = '敌人拿你一张牌'
                                                                steal_card = random.choice(Player_T.hand_cards)
                                                                if steal_card.is_protected:
                                                                    pass
                                                                else:
                                                                    Bot.hand_cards.append(steal_card)
                                                                    Player_T.hand_cards.remove(steal_card)
                                                                    i.skill_complete = True

                                                            else:
                                                                messages = '你拿对方一张牌'
                                                                if chosed_card == None:
                                                                    chosed_card = True
                                                                elif chosed_card == True:
                                                                    pass
                                                                else:
                                                                    if chosed_card.is_protected:
                                                                        chosed_card = True
                                                                    else:
                                                                        Player_T.hand_cards.append(chosed_card)
                                                                        Bot.hand_cards.remove(chosed_card)
                                                                        i.skill_complete = True
                                                                        chosed_card = None

                                                        # 女祭司 使即时发动的技能延迟到结束时发动
                                                        elif c_name == '02':
                                                            if active_card.is_on:
                                                                pass
                                                            else:
                                                                pass
                                                            i.skill_complete = True

                                                        # 皇后 多摸一张手牌
                                                        elif c_name == '03':
                                                            if (i == Bot and active_card.is_on or
                                                                    i == Player_T and not active_card.is_on):
                                                                messages = '敌方抽张大阿卡纳牌'
                                                                # 机器人拿到皇后
                                                                Bot.get_cards(washed_cards, '大阿卡纳')
                                                                i.skill_complete = True
                                                            else:
                                                                messages = '请抽张阿卡纳牌'
                                                                if Player_T.can_get == False:
                                                                    Player_T.can_get = True
                                                                elif Player_T.can_get == 'OK':
                                                                    Player_T.can_get = False
                                                                    i.skill_complete = True

                                                        elif c_name == '04':
                                                            if active_card.is_on:
                                                                pass
                                                            else:
                                                                pass
                                                            i.skill_complete = True

                                                        elif c_name == '05':
                                                            if active_card.is_on:
                                                                pass
                                                            else:
                                                                pass
                                                            i.skill_complete = True

                                                        elif c_name == '06':
                                                            if active_card.is_on:
                                                                pass
                                                            else:
                                                                pass
                                                            i.skill_complete = True

                                                        elif c_name == '07':
                                                            if active_card.is_on:
                                                                pass
                                                            else:
                                                                pass
                                                            i.skill_complete = True

                                                        elif c_name == '08':
                                                            if active_card.is_on:
                                                                pass
                                                            else:
                                                                pass
                                                            i.skill_complete = True

                                                        elif c_name == '09':
                                                            if active_card.is_on:
                                                                pass
                                                            else:
                                                                pass
                                                            i.skill_complete = True

                                                        # 命运之轮重洗手牌
                                                        elif c_name == '10':
                                                            # 判断作用对象
                                                            if active_card.is_on:
                                                                skill_ob = i
                                                            else:
                                                                skill_ob = enemy
                                                            # 重置对象手牌状态
                                                            for wheel in skill_ob.hand_cards:
                                                                wheel.clean_card()
                                                                cards['弃牌堆'].remove(wheel)
                                                            skill_ob.hand_cards = []
                                                            skill_ob.get_card = False

                                                            # 重置对象的结束状态
                                                            skill_ob.gg = False

                                                            i.skill_complete = True

                                                        # 正义 保护自己及一张自己的手牌
                                                        elif c_name == '11':
                                                            if (i == Bot and active_card.is_on or
                                                                    i == Player_T and not active_card.is_on):
                                                                messages = '敌人保一张牌'
                                                                protect_card = random.choice(Bot.hand_cards)
                                                                if protect_card.card_id == active_card.card_id:
                                                                    pass
                                                                else:
                                                                    protect_card.is_protected = True
                                                                    active_card.is_protected = True
                                                                    i.skill_complete = True
                                                            else:
                                                                messages = '你保一张牌'
                                                                if chosed_card_m == None:
                                                                    chosed_card_m = True
                                                                elif chosed_card_m == True:
                                                                    pass
                                                                else:
                                                                    if chosed_card_m != None:
                                                                        if chosed_card_m.card_id == active_card.card_id:
                                                                            chosed_card_m = True
                                                                        else:
                                                                            chosed_card_m.is_protected = True
                                                                            active_card.is_protected = True
                                                                            i.skill_complete = True
                                                                            chosed_card_m = None

                                                        # 倒吊人 弃对面一张牌
                                                        elif c_name == '12':
                                                            if (i == Bot and active_card.is_on or
                                                                    i == Player_T and not active_card.is_on):
                                                                messages = '敌人弃你一张牌'
                                                                destroy_card = random.choice(Player_T.hand_cards)
                                                                if destroy_card.is_protected:
                                                                    pass
                                                                else:
                                                                    Player_T.hand_cards.remove(destroy_card)
                                                                    destroy_card.is_open = False
                                                                    destroy_card.is_used = False
                                                                    destroy_card.point_ban = False
                                                                    destroy_card.effct_ban = False
                                                                    cards['弃牌堆'].remove(destroy_card)
                                                                    i.skill_complete = True

                                                            else:
                                                                messages = '你弃对方一张牌'
                                                                if chosed_card == None:
                                                                    chosed_card = True
                                                                elif chosed_card == True:
                                                                    pass
                                                                else:
                                                                    if chosed_card.is_protected:
                                                                        chosed_card = True
                                                                    else:
                                                                        Bot.hand_cards.remove(chosed_card)
                                                                        chosed_card.is_open = False
                                                                        chosed_card.is_used = False
                                                                        chosed_card.point_ban = False
                                                                        chosed_card.effct_ban = False
                                                                        cards['弃牌堆'].remove(chosed_card)
                                                                        i.skill_complete = True
                                                                        chosed_card = None

                                                        # 死亡 禁一张牌技能
                                                        elif c_name == '13':
                                                            if (i == Bot and active_card.is_on or
                                                                    i == Player_T and not active_card.is_on):
                                                                messages = '敌人禁你一张牌技能'
                                                                ban_p_card = random.choice(Player_T.hand_cards)
                                                                if ban_p_card.is_protected:
                                                                    pass
                                                                else:
                                                                    ban_p_card.effct_ban = True
                                                                    i.skill_complete = True
                                                            else:
                                                                messages = '你禁对方一张牌技能'
                                                                if chosed_card == None:
                                                                    chosed_card = True
                                                                elif chosed_card == True:
                                                                    pass
                                                                else:
                                                                    if chosed_card.is_protected:
                                                                        chosed_card = True
                                                                    else:
                                                                        chosed_card.effct_ban = True
                                                                        i.skill_complete = True
                                                                        chosed_card = None

                                                        elif c_name == '14':
                                                            if active_card.is_on:
                                                                pass
                                                            else:
                                                                pass
                                                            i.skill_complete = True

                                                        elif c_name == '15':
                                                            if active_card.is_on:
                                                                pass
                                                            else:
                                                                pass
                                                            i.skill_complete = True

                                                        # 塔 使牌的点数去除十位数.
                                                        elif c_name == '16':
                                                            if (i == Bot and active_card.is_on or
                                                                    i == Player_T and not active_card.is_on):
                                                                messages = '敌方选择作用对象'
                                                                ban_p_card = random.choice(Player_T.hand_cards)
                                                                if ban_p_card.is_protected:
                                                                    pass
                                                                else:
                                                                    ban_p_card.is_tower = True
                                                                    i.skill_complete = True
                                                            else:
                                                                messages = '你选择作用对象'
                                                                if chosed_card == None:
                                                                    chosed_card = True
                                                                elif chosed_card == True:
                                                                    pass
                                                                else:
                                                                    if chosed_card.is_protected:
                                                                        chosed_card = True
                                                                    else:
                                                                        chosed_card.is_tower = True
                                                                        i.skill_complete = True
                                                                        chosed_card = None
                                                        # 星星 看自己所有手牌
                                                        elif c_name == '17':
                                                            if (i == Bot and active_card.is_on or
                                                                    i == Player_T and not active_card.is_on):
                                                                messages = '敌方看自己牌'
                                                                i.skill_complete = True
                                                            else:
                                                                messages = '你看自己牌'
                                                                if seeing == None:
                                                                    card_status = []
                                                                    for see in Player_T.hand_cards:
                                                                        card_status.append(see.is_open)
                                                                        see.is_open = True
                                                                    seeing = True
                                                                elif seeing == True:
                                                                    (see_ok.width, see_ok.height,
                                                                     see_ok.x, see_ok.y) = (ww * 0.1245, wh * 0.0911,
                                                                                            ww * 0.4, wh * 0.49)
                                                                    see_ok.draw()
                                                                else:
                                                                    for t_b in range(0, len(card_status)):
                                                                        Player_T.hand_cards[t_b].is_open = card_status[t_b]
                                                                    i.skill_complete = True
                                                                    seeing = None

                                                        elif c_name == '18':
                                                            if active_card.is_on:
                                                                pass
                                                            else:
                                                                pass
                                                            i.skill_complete = True

                                                        # 太阳 看对方的所有牌
                                                        elif c_name == '19':
                                                            if (i == Bot and active_card.is_on or
                                                                    i == Player_T and not active_card.is_on):
                                                                messages = '敌方看你牌'
                                                                i.skill_complete = True
                                                            else:
                                                                messages = '你看敌方牌'
                                                                if seeing == None:
                                                                    card_status = []
                                                                    for see in Bot.hand_cards:
                                                                        card_status.append(see.is_open)
                                                                        see.is_open = True
                                                                    seeing = True
                                                                elif seeing == True:
                                                                    (see_ok.width, see_ok.height,
                                                                     see_ok.x, see_ok.y) = (ww * 0.1245, wh * 0.0911,
                                                                                            ww * 0.4, wh * 0.49)
                                                                    see_ok.draw()
                                                                else:
                                                                    for t_b in range(0, len(card_status)):
                                                                        Bot.hand_cards[t_b].is_open = card_status[t_b]
                                                                    i.skill_complete = True
                                                                    seeing = None


                                                        elif c_name == '20':
                                                            if (i == Bot and active_card.is_on or
                                                                    i == Player_T and not active_card.is_on):
                                                                messages = '敌方禁一张牌点'
                                                                ban_p_card = random.choice(Player_T.hand_cards)
                                                                if ban_p_card.is_protected:
                                                                    pass
                                                                else:
                                                                    ban_p_card.point_ban = True
                                                                    i.skill_complete = True

                                                            else:
                                                                messages = '你禁一张牌点'
                                                                if chosed_card == None:
                                                                    chosed_card = True
                                                                elif chosed_card == True:
                                                                    pass
                                                                else:
                                                                    if chosed_card.is_protected:
                                                                        chosed_card = True
                                                                    else:
                                                                        chosed_card.point_ban = True
                                                                        i.skill_complete = True
                                                                        chosed_card = None

                                                        # 世界 反转所有牌
                                                        elif c_name == '21':
                                                            if active_card.is_on:
                                                                pass
                                                            else:
                                                                pass
                                                            i.skill_complete = True

                                                        else:
                                                            pass
                                                elif active_card.effct_ban:
                                                    # 判定完翻完牌但牌技能被禁
                                                    i.skill_complete = True

                                                else:
                                                    # 判定完翻完牌但没有技能牌
                                                    pass
                                            else:
                                                # 判定完毕但是没翻牌
                                                if i == Bot:
                                                    # 如果是机器人
                                                    for closed in Bot.hand_cards:
                                                        if not closed.is_open:
                                                            closed.is_open = True
                                                            touch_card_s.play()
                                                            active_card = closed
                                                            break
                                                    i.turn_complete = True
                                        else:
                                            # 判定未结束
                                            pass
                                    elif i.is_active and i.gg:
                                        # 计算未翻开手牌数量
                                        no_use = len(i.hand_cards)
                                        for no_used in i.hand_cards:
                                            if no_used.is_used:
                                                no_use -= 1

                                        if no_use == 0:
                                            i.is_active = False
                                            i.turn_complete = False
                                            i.skill_complete = False
                                            i.gg = True
                                            print(i.name + '结束了')
                                            for j in names:
                                                if j != i:
                                                    j.is_active = True
                                            over_game = time.time()
                                        else:
                                            i.gg = False

        else:
            pass

    elif gui == 'overgame':
        card_size = (ww * 0.0779, wh * 0.2395)
        screen.blit(bg, (0, 0))

        # 判断胜利方
        if game_winner == None:
            if Bot.points > Player_T.points:
                game_res = '失败'
                og_title_color = (196, 7, 7)
            elif Bot.points < Player_T.points:
                game_res = '胜利'
                og_title_color = (255, 216, 61)
            else:
                game_res = '平局'
                og_title_color = (255, 98, 0)
        else:
            if game_winner == Bot:
                game_res = '失败'
                og_title_color = (196, 7, 7)
            else:
                game_res = '胜利'
                og_title_color = (255, 216, 61)

        # 结算界面标题
        overgame_title = Text(int(fr * 140), game_res, ww * 0.504, wh * 0.135, color=og_title_color)
        overgame_title.draw()

        # 返回主界面按钮
        go_back_b.width, go_back_b.height, go_back_b.x, go_back_b.y = (ww * 0.11, wh * 0.08,
                                                                       ww * 0.448, wh * 0.9)
        go_back_b.font_size = int(fr * 40)
        go_back_b.draw()

        # 绘制身份牌及ID
        iden_x, i_deny = ww * 0.07, wh * 0.30
        name_x, name_y = ww * 0.148, wh * 0.267
        if game_res == '胜利':
            p_color = (255, 216, 61)
            b_color = (196, 7, 7)
        elif game_res == '失败':
            p_color = (196, 7, 7)
            b_color = (255, 216, 61)
        else:
            p_color = (255, 98, 0)
            b_color = (255, 98, 0)

        for i in [Bot, Player_T]:
            if i == Bot:
                id_color = b_color
            else:
                id_color = p_color
            name_text = Text(int(fr * 44), i.name, name_x, name_y, color=id_color)
            name_text.draw()

            i.identity_card.x, i.identity_card.y = iden_x, i_deny
            i.identity_card.width, i.identity_card.height = card_size[0] * 2, card_size[1] * 2
            i.identity_card.draw()
            iden_x += ww * 0.485
            name_x += ww * 0.485

        # 载文字条
        text_bar = transform_scale(img_ui['载文字条.png'], ww * 0.23, wh * 0.013)
        text_bar_blit_num = 0
        text_bar_x, text_bar_y = ww * 0.258, wh * 0.374

        project_text = ['点数:', '手牌:', '翻牌:', '点数:', '手牌:', '翻牌:']
        project_text_num = 0

        for i in range(0, 6):
            screen.blit(text_bar, (text_bar_x, text_bar_y))
            opened_card_nums = 0
            if i <= 2:
                p_ob = 0
                pj_text_color = b_color
            else:
                p_ob = 1
                pj_text_color = p_color

            if project_text[project_text_num] == '点数:':
                info_text = str(names[p_ob].points)
            elif project_text[project_text_num] == '手牌:':
                info_text = str(len(names[p_ob].hand_cards))
            else:
                for opened_card_num in names[p_ob].hand_cards:
                    if opened_card_num.is_open:
                        opened_card_nums += 1
                info_text = str(opened_card_nums)

            fight_info = Text(int(fr * 52), info_text, text_bar_x + ww * 0.14,
                              text_bar_y - wh * 0.04, color=pj_text_color)
            project_text_ob = Text(int(fr * 40), project_text[project_text_num],
                                   text_bar_x + ww * 0.035, text_bar_y - wh * 0.04,
                                   color=pj_text_color)

            project_text_ob.draw()
            fight_info.draw()
            project_text_num += 1
            text_bar_blit_num += 1

            if text_bar_blit_num == 3:
                text_bar_x += ww * 0.485
                text_bar_y = wh * 0.37
            else:
                text_bar_y += wh * 0.2

    elif gui == 'chose_identity':
        # 刷新页面组件的信息
        if skin['back'] == 'bili':
            img = img_bili
        elif skin['back'] == 'rider':
            img = img_rider
        else:
            img = img_rider

        chose_title.font_size = int(fr * 80)
        chose_title.x, chose_title.y = ww * 0.51, wh * 0.25

        chose_title2.font_size = int(70 * fr)
        chose_title2.x, chose_title2.y = ww * 0.51, wh * 0.25

        # 调整卡片大小
        card_size = (ww * 0.0974, wh * 0.2994)
        for i in cards.keys():
            for j in cards[i]:
                j.width = card_size[0]
                j.height = card_size[1]

        screen.blit(bg, (0, 0))
        card_x = ww * 0.0952
        card_y = wh * 0.4297

        for i in cards['ace']:
            i.x, i.y = card_x, card_y
            i.draw()
            card_x += ww * 0.1047

        if start_game:
            time_differ = time.time() - start_game
            if time_differ >= data['start_fight']:
                gui = 'fighting'
            else:
                content = '将在{:.1f}秒后进入对局...'.format(data['start_fight'] - time_differ)
                chose_timer = Text(int(50 * fr), content, ww * 0.54, wh * 0.86,
                                   color=title_chose_color)
                chose_timer.draw()
                chose_title2.draw()
        else:
            chose_title.draw()

    elif gui == 'skin_chose':
        pass

    elif gui == 'login':
        pass

    for event in pg.event.get():
        # 更新按钮状态
        for i in button_home:
            i.check_status()
        save_cg.check_status()
        go_back_b.check_status()
        see_ok.check_status()

        if event.type == MOUSEBUTTONDOWN:
            if gui == 'setting':
                for i in slide_bars_active.keys():
                    rect = g_rect(i)
                    if rect.collidepoint(event.pos):
                        slide_bars_active[i] = True

        elif event.type == MOUSEBUTTONUP:
            if gui == 'home':
                # 背景音量键
                if g_rect(sound_bg).collidepoint(event.pos):
                    data['music_switch'] = not data['music_switch']
                    button_sd.play()
                    save_config(data)
                    sound_icon(data['music_switch'])

                # 设置键
                elif g_rect(button_home[2]).collidepoint(event.pos):
                    button_sd.play()
                    gui = 'setting'

                # 多人模式键
                elif g_rect(button_home[1]).collidepoint(event.pos):
                    button_sd.play()

                # 单人模式键
                elif g_rect(button_home[0]).collidepoint(event.pos):
                    button_sd.play()
                    gui = 'chose_identity'
                    pg.mixer.music.stop()
                    pg.mixer.music.load(music_directory + '/CalabiYau/' + '概率论.mp3')
                    pg.mixer.music.set_volume(data['setting']['背景音量'])
                    pg.mixer.music.play(-1)

            elif gui == 'setting':
                rect = g_rect(save_cg)
                if rect.collidepoint(event.pos):
                    button_sd.play()
                    gui = 'home'

                for i in slide_bars_active.keys():
                    rect = g_rect(i)
                    if rect.collidepoint(pg.mouse.get_pos()):
                        button_sd.play()
                        slide_bars_active[i] = False

            elif gui == 'chose_identity':
                if not Player_T.identity_chosen:
                    hit_card = None
                    for i in cards['ace']:
                        if Player_T.identity_chosen:
                            Player_T.identity_card = hit_card
                            start_game = time.time()
                            chose_title2.text = '你抽到了 ' + Player_T.identity_card.card_id.split('.')[0]
                        else:
                            Player_T.identity_chosen = i.turn_on_card('on')
                            touch_card_s.play()
                            hit_card = i
                            cards['弃牌堆'].append(i)

            elif gui == 'fighting':
                washed_cards = wash_cards(cards['大阿卡纳'])

                # 摸初始牌
                if not Player_T.get_card:
                    Player_T.get_cards(washed_cards, '大阿卡纳')
                    if data['cards_min'] == len(Player_T.hand_cards):
                        start_game = time.time()
                        Player_T.get_card = True

                        # for abc in cards['大阿卡纳']:
                        #     if abc.card_id == '17星星.png':
                        #         abc.is_on = True
                        #         cards['弃牌堆'].append(abc)
                        #         Player_T.hand_cards.append(abc)

                else:
                    # 猜拳
                    if (not gf_winner and
                            not Player_T.is_first and
                            not Bot.is_first):
                        if start_gf:
                            for player_chose in range(0, 3):
                                rect = g_rect(buttons[player_chose])
                                if rect.collidepoint(event.pos):
                                    Bot_result = random.choice([0, 1, 2])
                                    player_chosed = player_chose
                                    over_gf = time.time()
                    # 翻牌
                    if (Player_T.is_active and
                            Player_T.can_get == False):
                        if active_card:
                            if active_card.is_used:
                                for i in cards['大阿卡纳']:
                                    if i in Player_T.hand_cards:
                                        turned_card = i.turn_on_card('on')
                                        if turned_card:
                                            touch_card_s.play()
                                            active_card = i
                                            Player_T.turn_complete = True
                        else:
                            for i in cards['大阿卡纳']:
                                if i in Player_T.hand_cards:
                                    turned_card = i.turn_on_card('on')
                                    if turned_card:
                                        touch_card_s.play()
                                        active_card = i
                                        Player_T.turn_complete = True

                    # 选敌人的牌
                    if chosed_card == True:
                        for i in Bot.hand_cards:
                            if g_rect(i).collidepoint(event.pos):
                                touch_card_s.play()
                                chosed_card = i

                    # 选自己的牌
                    elif chosed_card_m == True:
                        for i in Player_T.hand_cards:
                            if g_rect(i).collidepoint(event.pos):
                                touch_card_s.play()
                                chosed_card_m = i

                    # 摸牌
                    if Player_T.can_get == True:
                        get_after = len(Player_T.hand_cards)
                        Player_T.get_cards(washed_cards, '大阿卡纳')
                        if len(Player_T.hand_cards) - get_after == 1:
                            Player_T.can_get = 'OK'

                    # 看牌
                    if seeing == True:
                        if g_rect(see_ok).collidepoint(event.pos):
                            seeing = False

            elif gui == 'overgame':
                if g_rect(go_back_b).collidepoint(event.pos):
                    button_sd.play()
                    gui = 'home'
                    # 清除猜拳数据
                    gf_winner = None
                    player_chosed = None
                    Bot_result = None
                    # 清除卡牌数据
                    cards['弃牌堆'] = []
                    for i in cards.keys():
                        for j in cards[i]:
                            j.clean_card()
                    # 洗身份牌
                    cards['ace'] = wash_cards(cards['ace'])
                    # 清除玩家数据
                    Bot = Player('Bot')
                    Player_T = Player('Edwad_过客')
                    names = [Bot, Player_T]
                    # 清除游戏状态数据
                    game_winner = None
                    start_game = None
                    active_card = None

        elif event.type == MOUSEMOTION:
            if gui == 'setting':
                for i in slide_bars_active.keys():
                    if slide_bars_active[i]:
                        mouse_pos = event.pos
                        bar_length = i.width * 0.91 - i.width * 0.67
                        setting_rate = mouse_pos[0] - i.x - i.width * 0.67
                        # 检测范围
                        if setting_rate <= 0:
                            i.rate = 0
                        elif setting_rate >= bar_length:
                            i.rate = 1
                        else:
                            i.rate = float('{:.2f}'.format(setting_rate / bar_length))
                        data['setting'][i.text] = i.rate
                        save_config(data)

        if event.type == QUIT:
            pg.quit()
            sys.exit()
    pg.display.flip()
