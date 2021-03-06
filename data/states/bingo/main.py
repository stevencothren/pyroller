"""Main bingo game state"""

import time
import sys
import random
from collections import OrderedDict

import pygame as pg

from data import tools, prepare
from data.components.labels import NeonButton
from data.components import common
from data.prepare import BROADCASTER as B
from . import statemachine
from . import playercard
from . import dealercard
from . import patterns
from . import ballmachine
from . import cardselector
from . import events
from . import bingocard
from . import moneydisplay
from . import bonusdisplay
from . import bonusbuttons
from .settings import SETTINGS as S


class Bingo(statemachine.StateMachine):
    """State to represent a bing game"""
    name = "bingo"
    show_in_lobby = True

    def __init__(self):
        """Initialise the bingo game"""
        #
        self.verbose = False
        self.sound_muted = prepare.ARGS['debug']
        #
        self.screen_rect = pg.Rect((0, 0), prepare.RENDER_SIZE)
        self.auto_pick = S['debug-auto-pick']
        #
        self.ui = common.ClickableGroup()
        #
        self.lobby_button = NeonButton(S['lobby-position'], 'Lobby', self.return_to_lobby)
        self.new_game_button = NeonButton(S['new-game-position'], 'New', lambda x: self.restart_game(None, None))
        #
        # The controls to allow selection of different numbers of cards
        self.card_selector = cardselector.CardSelector('card-selector', self)
        self.card_selector.linkEvent(events.E_NUM_CARDS_CHANGED, self.change_number_of_cards)
        self.ui.append(self.card_selector.ui)
        #
        self.create_card_collection()
        self.ui.extend(self.cards)
        #
        self.winning_pattern = patterns.PATTERNS[0]
        #
        self.pattern_buttons = common.DrawableGroup()
        self.debug_buttons = common.DrawableGroup()
        self.buttons = common.DrawableGroup([self.pattern_buttons])
        #
        if prepare.DEBUG:
            self.buttons.append(self.debug_buttons)
        #
        super(Bingo, self).__init__()
        #
        # The machine for picking balls
        self.ball_machine = ballmachine.BallMachine('ball-machine', self)
        self.ball_machine.start_machine()
        self.ui.append(self.ball_machine.buttons)
        #
        self.all_cards = common.DrawableGroup()
        self.all_cards.extend(self.cards)
        self.all_cards.extend(self.dealer_cards)
        #
        B.linkEvent(events.E_PLAYER_PICKED, self.player_picked)
        B.linkEvent(events.E_PLAYER_UNPICKED, self.player_unpicked)
        B.linkEvent(events.E_CARD_COMPLETE, self.card_completed)
        #
        self.current_pick_sound = 0
        self.last_pick_time = 0

    @staticmethod
    def initialize_stats():
        """Return OrderedDict suitable for use in game stats

        :return: collections.OrderedDict
        """
        stats = OrderedDict([("games played", 0),
                             ("cards won", 0),
                             ("cards lost", 0),
                             ("total lost", 0),
                             ("total won", 0),
                             ("time played", '00:00:00'),
                             ("_last squares", [])])
        return stats

    def startup(self, current_time, persistent):
        """This method will be called each time the state resumes."""
        self.persist = persistent
        self.casino_player = self.persist["casino_player"]
        self.casino_player.current_game = self.name
        #
        self.casino_player.increase('games played')
        self.cards.set_card_numbers(self.casino_player.get('_last squares', []))
        self.money_display.set_money(self.casino_player.cash)
        self.time_started = time.time()

    def get_event(self, event, scale=(1,1)):
        """Check for events"""
        super(Bingo, self).get_event(event, scale)
        self.lobby_button.get_event(event)
        self.new_game_button.get_event(event)
        #
        if event.type == pg.QUIT:
            if prepare.ARGS['straight']:
                pg.quit()
                sys.exit()
            else:
                self.done = True
                self.next = "lobby"
        elif event.type in (pg.MOUSEBUTTONDOWN, pg.MOUSEMOTION):
            #
            self.ui.process_events(event, scale)
            self.bonus_buttons.process_events(event, scale)
            #
            pos = tools.scaled_mouse_pos(scale, event.pos)
        elif event.type == pg.KEYUP:
            if event.key == pg.K_ESCAPE:
                self.done = True
                self.next = "lobby"
            elif event.key == pg.K_SPACE:
                self.next_chip(None, None)
            elif event.key == pg.K_m:
                #self.persist["music_handler"].mute_unmute_music()
                self.sound_muted = not self.sound_muted
            elif event.key == pg.K_f:
                for card in self.cards:
                    self.add_generator('flash-labels', card.flash_labels())

    def return_to_lobby(self, arg):
        """Return to the lobby screen"""
        self.game_started = False
        self.done = True
        self.next = "lobby"
        self.casino_player.set('_last squares', self.cards.get_card_numbers())
        self.casino_player.cash = self.money_display.amount
        self.casino_player.increase_time('time played', time.time() - self.time_started)

    def drawUI(self, surface, scale):
        """Update the main surface once per frame"""
        mouse_pos = tools.scaled_mouse_pos(scale, pg.mouse.get_pos())
        self.lobby_button.update(mouse_pos)
        self.new_game_button.update(mouse_pos)
        #
        surface.fill(S['table-color'])
        #
        self.lobby_button.draw(surface)
        self.new_game_button.draw(surface)
        self.all_cards.draw(surface)
        self.ball_machine.draw(surface)
        self.buttons.draw(surface)
        self.card_selector.draw(surface)
        self.money_display.draw(surface)
        self.bonus_display.draw(surface)
        self.bonus_buttons.draw(surface)

    def initUI(self):
        """Initialise the UI display"""
        #
        # Buttons that show the winning patterns
        x, y = S['winning-pattern-position']
        for idx, pattern in enumerate(patterns.PATTERNS):
            dx, dy = S['winning-pattern-buttons'][pattern.name]
            new_button = patterns.PatternButton(
                idx, (x + dx, y + dy),
                'bingo-wide-red-button', 'bingo-wide-red-button-off', 'winning-pattern',
                pattern.name,
                pattern == self.winning_pattern, S,
                scale=S['winning-pattern-scale']
            )
            new_button.linkEvent(common.E_MOUSE_CLICK, self.change_pattern, pattern)
            new_button.pattern = pattern
            self.pattern_buttons.append(new_button)
        self.ui.extend(self.pattern_buttons)
        #
        # Simple generator to flash the potentially winning squares
        self.add_generator('potential-winners', self.flash_potential_winners())
        #
        # Display of the money the player has
        self.money_display = moneydisplay.MoneyDisplay(
            'money-display', S['money-position'], 0, self
        )
        prepare.BROADCASTER.linkEvent(events.E_SPEND_MONEY, self.spend_money)
        #
        # Button for next chip
        self.next_chip_button = common.ImageOnOffButton(
                'next-chip', S['next-chip-position'],
                'bingo-next-chip-on', 'bingo-next-chip-off', 'next-chip',
                'Next Chip (SPC)', True,
                S, scale=S['next-chip-scale']
        )
        self.next_chip_button.linkEvent(common.E_MOUSE_CLICK, self.next_chip)
        self.ui.append(self.next_chip_button)
        self.buttons.append(self.next_chip_button)
        #
        # Menu bar
        self.menu_bar = common.NamedSprite(
            'bingo-menu-bar', S['menu-bar-position'], scale=S['menu-bar-scale']
        )
        self.buttons.append(self.menu_bar)
        #
        self.bonus_display = bonusdisplay.BonusDisplay(
            'bonus-display', S['bonus-light-position'], self)
        #
        self.bonus_buttons = bonusbuttons.BonusButtonsDisplay(
            'bonus-buttons', S['bonus-buttons-position'], self
        )
        self.bonus_display.linkEvent(
            events.E_BONUS_REACHED,
            lambda o, a: self.bonus_buttons.pick_new_button()
        )
        #
        # Debugging buttons
        if prepare.DEBUG and S['show-debug-buttons']:
            self.debug_buttons.append(common.ImageOnOffButton(
                'auto-pick', S['debug-auto-pick-position'],
                'bingo-yellow-button', 'bingo-yellow-off-button', 'small-button',
                'Auto pick',
                S['debug-auto-pick'],
                S, scale=S['small-button-scale']
            ))
            self.debug_buttons[-1].linkEvent(common.E_MOUSE_CLICK, self.toggle_auto_pick)
            #
            self.debug_buttons.append(common.ImageButton(
                'restart', S['debug-restart-position'],
                'bingo-yellow-button', 'small-button',
                'Restart',
                S, scale=S['small-button-scale']
            ))
            self.debug_buttons[-1].linkEvent(common.E_MOUSE_CLICK, self.restart_game)
            #
            self.debug_buttons.append(common.ImageButton(
                'next-ball', S['debug-next-ball-position'],
                'bingo-yellow-button', 'small-button',
                'Next Ball',
                S, scale=S['small-button-scale']
            ))
            self.debug_buttons[-1].linkEvent(common.E_MOUSE_CLICK, self.next_ball)
            #
            self.debug_buttons.append(common.ImageButton(
                'new-cards', S['debug-new-cards-position'],
                'bingo-yellow-button', 'small-button',
                'New Cards',
                S, scale=S['small-button-scale']
            ))
            self.debug_buttons[-1].linkEvent(common.E_MOUSE_CLICK, self.draw_new_cards)
            self.ui.extend(self.debug_buttons)

    def spend_money(self, amount, arg):
        """Money has been spent"""
        self.log.info('Money has been spent {1} by {0}'.format(arg, amount))
        self.money_display.add_money(amount)
        if amount < 0:
            self.play_sound('bingo-pay-money')
            self.casino_player.increase('total lost', -amount)
        else:
            self.casino_player.increase('total won', amount)

    def change_pattern(self, obj, pattern):
        """Change the winning pattern"""
        self.log.info('Changing pattern to {0}'.format(pattern.name))
        #
        # Account for the random factor
        if pattern.name == "Random":
            self.add_generator(
                'randomize-buttons',
                self.randomly_highlight_buttons(
                    self.pattern_buttons[-1],
                    self.pattern_buttons[:-1],
                    S['randomize-button-number'], S['randomize-button-delay'],
                    lambda b: self.change_pattern(None, b.pattern)
                )
            )
            return
        #
        self.winning_pattern = pattern
        self.highlight_patterns(self.winning_pattern, one_shot=True)
        #
        # Clear all flashing squares
        for card in self.all_cards:
            card.potential_winning_squares = []
            for square in card.squares.values():
                square.is_focused = False
        #
        # Update UI
        for button in self.pattern_buttons:
            button.state = (button.pattern == self.winning_pattern)

    def toggle_auto_pick(self, obj, arg):
        """Toggle whether we are auto-picking numbers"""
        self.log.debug('Toggling auto-pick')
        self.auto_pick = not self.auto_pick
        self.debug_buttons[0].state = self.auto_pick

    def restart_game(self, obj, arg):
        """Restart the game"""
        self.log.info('Restart game')
        self.ball_machine.reset_machine(self.ball_machine.interval)
        self.cards.reset()
        self.dealer_cards.reset()
        self.current_pick_sound = 0
        self.last_pick_time = 0
        self.casino_player.increase('games played')

    def next_ball(self, obj, arg):
        """Move on to the next ball

        This is a debugging method - no using the normal UI

        """
        self.ball_machine.call_next_ball()

    def next_chip(self, obj, arg):
        """Move on to the next ball"""
        if self.next_chip_button.state:
            self.ball_machine.call_next_ball()
            self.add_generator('next-chip-animation', self.animate_next_chip())

    def animate_next_chip(self):
        """Animate the button after choosing another chip"""
        self.next_chip_button.state = False
        yield S['next-chip-delay'] * 1000
        self.next_chip_button.state = True

    def draw_new_cards(self, obj,  arg):
        """Draw a new set of cards"""
        self.log.debug('Drawing new set of cards')
        self.cards.draw_new_numbers()
        self.cards.reset()

    def create_card_collection(self):
        """Return a new card collection"""
        number = self.card_selector.number_of_cards
        self.cards = playercard.PlayerCardCollection(
            'player-card',
            S['player-cards-position'],
            S['player-card-offsets'][number],
            self
        )
        dx, dy = S['dealer-card-offset']
        dealer_offsets = [(dx + x, dy +y) for x, y in S['player-card-offsets'][number]]
        self.dealer_cards = dealercard.DealerCardCollection(
            'dealer-card',
            S['player-cards-position'],
            dealer_offsets,
            self
        )

    def change_number_of_cards(self, number, arg=None):
        """Change the number of cards in play"""
        self.log.info('Changing the number of cards to {0}'.format(number))
        #
        # Store off the old card number to reuse
        self.casino_player.set('_last squares', self.cards.get_card_numbers())
        #
        # Remove old cards
        for card in self.cards:
            self.all_cards.remove(card)
            self.ui.remove(card)
        for card in self.dealer_cards:
            self.all_cards.remove(card)
        #
        # Create new cards
        self.create_card_collection()
        self.cards.set_card_numbers(self.casino_player.get('_last squares', []))
        #
        self.all_cards.extend(self.cards)
        self.all_cards.extend(self.dealer_cards)
        self.ui.extend(self.cards)
        self.restart_game(None, None)

    def highlight_patterns(self, pattern, one_shot):
        """Test method to cycle through the winning patterns"""
        self.log.debug('Creating new highlight pattern generators')
        for card in self.cards:
            self.add_generator(
                'highlight-patterns-card-%s' % card.name,
                self.highlight_pattern(card, pattern, one_shot)
            )

    def highlight_pattern(self, card, pattern, one_shot):
        """Highlight a particular pattern on a card"""
        for squares in pattern.get_matches(card):
            for square in squares:
                square.highlighted_state = bingocard.S_GOOD
            card.set_dirty()
            yield 100
            for square in squares:
                square.highlighted_state = bingocard.S_NONE
            card.set_dirty()
            yield 10
        #
        if not one_shot:
            self.add_generator('highlight', self.highlight_pattern(card, pattern, one_shot=False))

    def ball_picked(self, ball):
        """A ball was picked"""
        # Turn off the button to prevent the player from accidentally choosing another
        # ball at the same time
        self.add_generator('next-chip-animation', self.animate_next_chip())
        #
        # If auto-picking then update the cards
        auto_pick_cards = list(self.dealer_cards)
        if self.auto_pick:
            auto_pick_cards.extend(self.cards)
        for card in auto_pick_cards:
            card.call_square(ball.number)
        #
        # Highlight the card labels
        for card in self.all_cards:
            card.highlight_column(ball.letter)

    def player_picked(self, square, arg):
        """The player picked a square"""
        if not square.card.is_active:
            return
        #
        self.bonus_display.add_bonus()
        #
        # Check to see if we created a new potentially winning square
        called_squares = list(square.card.called_squares)
        prior_called_squares = list(called_squares)
        prior_called_squares.remove(square.text)
        #
        _, winners = self.winning_pattern.get_number_to_go_and_winners(square.card, called_squares)
        _, prior_winners = self.winning_pattern.get_number_to_go_and_winners(square.card, prior_called_squares)
        self.log.debug('{0} / {1}'.format(winners, prior_winners))
        #
        if len(winners) > len(prior_winners):
            self.play_sound('bingo-potential-winner')
        #
        # Increment sound if we did this quickly
        if time.time() - self.last_pick_time < S['player-pick-interval']:
            self.current_pick_sound = min(self.current_pick_sound + 1, len(S['player-pick-sounds']) - 1)
        else:
            self.current_pick_sound = 0
        self.last_pick_time = time.time()
        self.play_sound(S['player-pick-sounds'][self.current_pick_sound])
        #
        self.log.info('Player picked {0}'.format(square))

    def player_unpicked(self, square, arg):
        """The player unpicked a square"""
        self.log.info('Player unpicked {0}'.format(square))
        self.play_sound('bingo-unpick')

    def flash_potential_winners(self):
        """Flash the squares that are potential winners"""
        while True:
            for state, delay in S['card-focus-flash-timing']:
                for card in self.all_cards:
                    potential_squares = card.potential_winning_squares
                    if potential_squares:
                        for square in potential_squares:
                            square.is_focused = state
                        card.set_dirty()
                yield delay * 1000

    def play_sound(self, name):
        """Play a named sound - respects the mute settings"""
        if not self.sound_muted:
            prepare.SFX[name].play()

    def get_missing_squares(self, squares):
        """Return a list of the numbers that have not been called"""
        return [square for square in squares if square.text not in self.ball_machine.called_balls]

    def card_completed(self, card, arg):
        """A card was completed"""
        self.log.info('Card {0} owned by {1} was completed'.format(card.index, card.card_owner))
        #
        if card.card_owner == bingocard.T_PLAYER:
            self.casino_player.increase('cards won' if card.card_state == bingocard.S_WON else 'cards lost')
        else:
            self.casino_player.increase('cards won' if card.card_state == bingocard.S_LOST else 'cards lost')
        #
        # Find the matching card from the dealer or player and deactivate it
        other_card = self.cards[card.index] if card.card_owner == bingocard.T_DEALER else self.dealer_cards[card.index]
        other_card.active = False
        other_card.set_card_state(bingocard.S_LOST)
        #
        # Check for all cards done
        for item in self.cards:
            if item.active and item != card:
                return
        else:
            for item in self.cards:
                self.add_generator('flash-labels', item.flash_labels())

    def randomly_highlight_buttons(self, source_button, buttons, number_of_times, delay, final_callback, speed_up=None,
                                   states=(False, True)):
        """Randomly highlight buttons in a group and then call the callback when complete"""
        false_state, true_state = states
        last_chosen = None
        if source_button:
            source_button.state = true_state
        #
        # Turn all buttons off
        for button in buttons:
            button.state = false_state
        #
        for i in range(number_of_times):
            #
            # Choose one to highlight, but not the last one
            while True:
                chosen = random.choice(buttons)
                if chosen != last_chosen:
                    break
            #
            # Highlight it
            self.log.debug('Setting to button {0}, {1}'.format(buttons.index(chosen), chosen.name))
            chosen.state = true_state
            if last_chosen:
                last_chosen.state = false_state
            last_chosen = chosen
            #
            self.play_sound('bingo-beep')
            #
            if i != number_of_times - 1:
                yield delay
            #
            # Shortern delay
            delay *= speed_up if speed_up else S['randomize-button-speed-up']
        #
        if source_button:
            source_button.state = false_state
        #
        final_callback(chosen)

    def pause_machine(self, delay):
        """Pause the ball machine for a certain length of time"""
        self.ball_machine.pause()

        def unpause():
            yield delay * 1000
            self.ball_machine.unpause()

        self.add_generator('un-pause', unpause())

    def double_up(self):
        """Double up all cards"""
        for card in self.cards:
            card.double_down()

    def slow_machine(self):
        """Slow the machine down"""
        self.ball_machine.change_speed(None, self.ball_machine.speed_transitions[0])

    def start_auto_pick(self, delay):
        """Temporarily auto pick the numbers"""
        self.auto_pick = True

        def unauto():
            yield delay * 1000
            self.auto_pick = False

        self.add_generator('un-auto', unauto())

    def win_card(self):
        """Win one of the cards"""
        possible_cards = [card for card in self.cards if card.active]
        if possible_cards:
            card = random.choice(possible_cards)
            card.set_card_state(bingocard.S_WON)
            self.play_sound(card.card_success_sound)
            B.processEvent((events.E_CARD_COMPLETE, card))
            card.active = False
