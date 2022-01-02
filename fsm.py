from transitions.extensions import GraphMachine
from transitions import State

import re
import random
from utils import *
from scraper import get_image_link

class TocMachine(GraphMachine):
    def state_enter(self,event):
        print("Enter " + self.state)

    def state_exit(self,event):
        print("Exit " + self.state)

    def set_environment(self,gold=1000):
        self.gold = gold
        self.cost = None
        self.deck = None
        self.cpu_hand = None
        self.hand = None

    def __init__(self):
        self.set_environment()
        states=[
            State(name='initial',on_enter=['state_enter'],on_exit=['state_exit']),
            State(name='start',on_enter=['state_enter'],on_exit=['state_exit']),
            State(name='bankrupt',on_enter=['state_enter'],on_exit=['state_exit']),
            State(name='coin_flip',on_enter=['state_enter'],on_exit=['state_exit']),
            State(name='ask_for_cost_flip',on_enter=['state_enter'],on_exit=['state_exit']),
            State(name='ask_for_cost_bj',on_enter=['state_enter'],on_exit=['state_exit']),
            State(name='draw_card',on_enter=['state_enter'],on_exit=['state_exit']),
            State(name='drawing_card',on_enter=['state_enter'],on_exit=['state_exit']),
            State(name='cpu_drawing_card',on_enter=['state_enter'],on_exit=['state_exit']),
            State(name='ask_for_retry',on_enter=['state_enter'],on_exit=['state_exit']),
            State(name='ask_for_retry_bj',on_enter=['state_enter'],on_exit=['state_exit']),
            State(name='black_jack',on_enter=['state_enter'],on_exit=['state_exit']),
            State(name='gold_add',on_enter=['state_enter'],on_exit=['state_exit']),
            ]
        GraphMachine.__init__(self,model=self,states=states,
                initial='initial',auto_transitions=False,show_conditions=True)

        self.add_transition(
                trigger='advance',
                source='initial',
                dest='gold_add',
                conditions='gold_add_message',
                )
        self.add_transition(
                'advance',
                '*',
                'initial',
                'go_back_to_user',
                )
        self.add_transition(
                'go_back',
                '*',
                'initial',
                )
        self.add_transition(
                'advance',
                '*',
                None,
                after='check_gold',
                conditions='gold_check_message',
                )
        self.add_transition(
                'advance',
                '*',
                None,
                after='check_state',
                conditions='state_check_message',
                )
        self.add_transition(
                'advance',
                'gold_add',
                None,
                after='add_gold',
                conditions='is_pos_digit',
                )
        self.add_transition(
                'advance',
                'initial',
                'start',
                'start_message',
                )
        self.add_transition(
                'advance',
                ['initial','start','coin_flip','black_jack','ask_for_retry'],
                'bankrupt',
                unless='has_gold',
                )
        self.add_transition(
                'advance',
                'start',
                'coin_flip',
                conditions='coin_message'
                )
        self.add_transition(
                'advance',
                'start',
                'black_jack',
                conditions='bj_message'
                )
        self.add_transition(
                'advance',
                'coin_flip',
                'ask_for_cost_flip',
                conditions='is_pos_digit',
                unless='more_than_budget'
                )
        self.add_transition(
                'advance',
                'black_jack',
                'ask_for_cost_bj',
                conditions='is_pos_digit',
                unless='more_than_budget'
                )
        self.add_transition(
                'advance',
                ['ask_for_cost_bj','draw_card'],
                'drawing_card',
                conditions='yes_condition',
                unless='bj_lose',
                )
        self.add_transition(
                'advance',
                ['ask_for_cost_bj','draw_card'],
                'cpu_drawing_card',
                conditions='no_condition',
                )
        self.add_transition(
                'advance',
                'ask_for_cost_flip',
                'ask_for_retry',
                conditions='head_or_tail_message',
                )
        self.add_transition(
                'advance',
                'ask_for_retry',
                'start',
                conditions='no_condition',
                )
        self.add_transition(
                'advance',
                'ask_for_retry',
                'coin_flip',
                conditions='yes_condition',
                )
        self.add_transition(
                'advance',
                'ask_for_retry_bj',
                'black_jack',
                conditions='yes_condition',
                )
        self.add_transition(
                'advance',
                'ask_for_retry_bj',
                'start',
                conditions='no_condition',
                )
        self.add_transition(
                'check_result',
                'cpu_drawing_card',
                'ask_for_retry_bj'
                )
        self.add_transition(
                'to_draw_card',
                'drawing_card',
                'draw_card',
                unless='bj_lose',
                )
        self.add_transition(
                'to_draw_card',
                'drawing_card',
                'ask_for_retry_bj',
                conditions='bj_lose',
                )
        self.add_transition(
                'to_draw_card',
                'drawing_card',
                'ask_for_retry_bj',
                conditions='bj_full',
                )

    def check_state(self,event):
        user_id = event.source.user_id
        msg = "Current : " + self.state
        push_message(user_id,msg)


    def add_gold(self,event):
        self.gold += int(event.message.text)
        self.go_back(event)

    def check_gold(self,event):
        user_id = event.source.user_id
        msg = "Gold : " + str(self.gold)
        push_message(user_id,msg)

    def on_enter_ask_for_cost_flip(self,event):
        user_id = event.source.user_id
        self.cost = int(event.message.text)
        send_confirm_message(user_id,"Pick a side",["head","tail"],["head","tail"])

    def on_enter_ask_for_cost_bj(self,event):
        user_id = event.source.user_id
        self.cost = int(event.message.text)
        self.hand = []
        self.cpu_hand = []
        self.deck = [value for value in ['A','2','3','4','5','6','7','8','9','10','J','Q','K']
                for _ in range(4)]
        random.shuffle(self.deck)
        for _ in range(2):
            self.cpu_hand.append(self.deck.pop())
            self.hand.append(self.deck.pop())

        msg = "CPU reveals\n" + self.cpu_hand[0]
        push_message(user_id,msg)
        msg = "Your hand is\n" + ' '.join(self.hand)
        push_message(user_id,msg)
        send_confirm_message(user_id,"Draw a card?",["Yes","No"],["Yes","No"])

    def hand_value(self,list_hand):
        value = 0
        suits = {
                'A': 1,
                '2': 2,
                '3': 3,
                '4': 4,
                '5': 5,
                '6': 6,
                '7': 7,
                '8': 8,
                '9': 9,
                '10':10,
                'J': 10,
                'Q': 10,
                'K': 10,
                }
        for hand in list_hand:
            value += suits[hand]
        return value


    def on_enter_cpu_drawing_card(self,event):
        while True:
            if self.hand_value(self.cpu_hand) >= 21 or self.hand_value(self.cpu_hand) > self.hand_value(self.hand):
                break
            else:
                self.cpu_hand.append(self.deck.pop())
        self.check_result(event)

    def on_enter_drawing_card(self,event):
        self.hand.append(self.deck.pop())
        self.to_draw_card(event)

    def on_enter_draw_card(self,event):
        user_id = event.source.user_id
        msg = "CPU reveals\n" + self.cpu_hand[0]
        push_message(user_id,msg)
        msg = "Your hand is\n" + ' '.join(self.hand)
        push_message(user_id,msg)
        send_confirm_message(user_id,"Draw a card?",["Yes","No"],["Yes","No"])

    def on_enter_ask_for_retry(self,event):
        user_id = event.source.user_id
        result = random.choice(["head","tail"])
        msg = "result is " + result
        push_message(user_id,msg)
        if result == event.message.text:
            msg = "You Won"
            self.gold += self.cost
        else:
            msg = "You Lost"
            self.gold -= self.cost
        push_message(user_id,msg)
        send_confirm_message(user_id,"Try again?",["Yes","No"],["yes","no"])

    def on_enter_ask_for_retry_bj(self,event):
        user_id = event.source.user_id
        msg = "CPU reveals\n" + ' '.join(self.cpu_hand)
        push_message(user_id,msg)
        msg = "Your hand is\n" + ' '.join(self.hand)
        push_message(user_id,msg)
        print(self.hand_value(self.hand),self.hand_value(self.cpu_hand))
        if self.hand_value(self.hand)>21 and self.hand_value(self.cpu_hand)>21:
            msg = "Draw"
        elif self.hand_value(self.hand)>21:
            msg = "You Lost"
            self.gold -= self.cost
        elif self.hand_value(self.cpu_hand)>21:
            msg = "You Won"
            self.gold += self.cost
        else:
            if self.hand_value(self.hand) > self.hand_value(self.cpu_hand):
                msg = "You Won"
                self.gold += self.cost
            elif  self.hand_value(self.hand) < self.hand_value(self.cpu_hand):
                msg = "You Lost"
                self.gold -= self.cost
            else:
                msg = "Draw"
        push_message(user_id,msg)
        send_confirm_message(user_id,"Try again?",["Yes","No"],["yes","no"])

    def on_enter_bankrupt(self,event):
        self.go_back(event)

    def on_exit_bankrupt(self,event):
        user_id = event.source.user_id
        msg = "Insufficient Funds";
        actions = [("ADD","add gold"),("RETURN","return to main menu")]
        send_quick_message_reply(user_id,msg,actions)

    def on_enter_gold_add(self,event):
        user_id = event.source.user_id
        msg = "How much? (Current=" + str(self.gold) + ")"
        send_quick_message_reply(user_id,msg,
                [("100","100"),("500","500"),("1000","1000"),
                    ("CHECK","check gold"),("RETURN","return to main menu")])

    def on_enter_start(self,event):
        user_id = event.source.user_id
        link1=get_image_link('blackjack')
        link2=get_image_link('coin')
        urls = [link1,link2]
        labels = ['blackjack','coin']
        txt = ['play blackjack','flip a coin']
        send_image_carousel(user_id,urls,labels,txt)

    def on_enter_coin_flip(self,event):
        user_id = event.source.user_id
        msg = "How much? (Current=" + str(self.gold) + ")"
        send_quick_message_reply(user_id,msg,
                [("half",str(int(self.gold/2))),("all",str(int(self.gold))),
                    ("CHECK","check gold"),("RETURN","return to main menu")])

    def on_enter_black_jack(self,event):
        user_id = event.source.user_id
        msg = "How much? (Current=" + str(self.gold) + ")"
        send_quick_message_reply(user_id,msg,
                [("half",str(int(self.gold/2))),("all",str(int(self.gold))),
                    ("CHECK","check gold"),("RETURN","return to main menu")])

    def start_message(self, event):
        text = event.message.text
        return text.lower() == "start"

    def coin_message(self,event):
        text = event.message.text
        return text.lower() == "flip a coin"

    def bj_message(self,event):
        text = event.message.text
        return text.lower() == "play blackjack"

    def gold_add_message(self, event):
        text = event.message.text
        return text.lower() == "add gold"

    def gold_check_message(self, event):
        text = event.message.text
        return text.lower() == "check gold"

    def state_check_message(self, event):
        text = event.message.text
        return text.lower() == "check state"

    def go_back_to_user(self,event):
        text = event.message.text
        return text.lower() == "return to main menu"

    def is_pos_digit(self,event):
        text = event.message.text
        return text.isdigit()

    def has_gold(self,event):
        return self.gold > 0

    def head_or_tail_message(self,event):
        text = event.message.text
        return text.lower() == "head" or text.lower() == "tail"

    def more_than_budget(self,event):
        text = event.message.text
        return (not text.isdigit()) or int(text) > self.gold

    def yes_condition(self,event):
        text = event.message.text
        return text.lower() == "yes"

    def no_condition(self,event):
        text = event.message.text
        return text.lower() == "no"

    def bj_full(self,event):
        value = self.hand_value(self.hand)
        return value == 21

    def bj_lose(self,event):
        value = self.hand_value(self.hand)
        return value > 21

