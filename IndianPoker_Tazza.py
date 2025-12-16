import random
import time
import os
import unicodedata

# --- 1. Card 클래스 ---
class Card:
    SUITS = {'S': '♠', 'D': '♦', 'H': '♥', 'C': '♣'}
    RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    VALUES = {r: i+2 for i, r in enumerate(RANKS)}

    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
        self.symbol = self.SUITS[suit]
        self.value = self.VALUES[rank]

    def __str__(self):
        return f"{self.symbol}{self.rank}"

    def get_ascii_art(self, hidden=False):
        if hidden:
            return ["┌─────────┐", "│░░░░░░░░░│", "│░░░░?░░░░│", "│░░░░░░░░░│", "└─────────┘"]
        r_str = f"{self.rank:<2}"
        return ["┌─────────┐", f"│{r_str}       │", f"│    {self.symbol}    │", f"│       {r_str}│", "└─────────┘"]

    def __gt__(self, other): return self.value > other.value
    def __eq__(self, other): return self.value == other.value


# --- 2. Deck 클래스 ---
class Deck:
    def __init__(self):
        self.cards = [Card(s, r) for s in Card.SUITS.keys() for r in Card.RANKS]
        self.shuffle()

    def shuffle(self): random.shuffle(self.cards)

    def draw(self):
        return self.cards.pop() if self.cards else None

    def extract_card(self, rank_str):
        for i, card in enumerate(self.cards):
            if card.rank == rank_str:
                return self.cards.pop(i)
        return None 


# --- 3. Game 클래스 ---
class IndianPokerGame:
    CHEAT_SUCCESS_RATE = 0.3 # 기술 성공 확률 30%

    def __init__(self):
        self.reset_game() # 초기화 로직 분리

    def reset_game(self):
        """게임을 처음 상태로 되돌립니다."""
        self.deck = Deck()
        self.p_chip = 20
        self.c_chip = 20
        self.starter = "Player"
        self.pot = 0

    def clear_screen(self):
        print("\n" * 2 + "═" * 70 + "\n")

    def slow_print(self, text, delay=0.05):
        print(text)
        time.sleep(delay)

    def print_lines_slow(self, lines, delay=0.05):
        for line in lines:
            print(line)
            time.sleep(delay)
    
    def _disp_width(self, s):
        width = 0
        for ch in s:
            if unicodedata.combining(ch): continue
            width += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
        return width

    def _pad_disp(self, s, target):
        return s + (" " * max(0, target - self._disp_width(s)))

    def print_rules(self):
        body_lines = [
            "🃏 INDIAN POKER: Tazza Edition",
            "[기본 룰] A > K > ... > 2, 상대 카드는 보이고 내 카드는 안 보임",
            "[타짜 룰] 딜러는 덱을 섞을 때 '기술(밑장빼기)' 사용 가능",
            f"         기술 성공 확률: {int(self.CHEAT_SUCCESS_RATE*100)}%",
            "         (상대방이 의심해서 걸리면 즉시 패배합니다!)",
            "--- 국제 표준 베팅 용어 ---",
        " [Check] 낼 돈이 없을 때 칩 소모 없이 턴 넘기기",
        " [Bet/Raise] 판돈을 키우기 위해 칩을 추가로 걸기",
        " [Call] 상대방이 건 칩만큼 내고 승부(카드 오픈)",
        " [Fold] 패가 안 좋으면 포기 (현재까지 건 돈 포기)",
        ]
        width = max(self._disp_width(line) for line in body_lines)
        top = "┏" + "━" * (width + 2) + "┓"
        mid = "┣" + "━" * (width + 2) + "┫"
        bottom = "┗" + "━" * (width + 2) + "┛"

        lines_to_show = [top, "┃ " + self._pad_disp(body_lines[0], width) + " ┃", mid]
        lines_to_show.extend("┃ " + self._pad_disp(line, width) + " ┃" for line in body_lines[1:])
        lines_to_show.append(bottom)
        self.print_lines_slow(lines_to_show, 0.02)

    def print_table(self, p_card, c_card, p_bet_amt, c_bet_amt, pot, show_mine=False, msg="", clear=True):
        if clear: self.clear_screen()
        c_art = c_card.get_ascii_art(hidden=False)
        p_art = p_card.get_ascii_art(hidden=not show_mine)

        lines = [
            f"\n [ COMPUTER ] 칩: {self.c_chip}  |  베팅: {c_bet_amt}",
            "=" * 64, "\n"
        ]
        for c, p in zip(c_art, p_art):
            lines.append(f"      {c}            {p}")
        lines.extend([
            "\n", "     [ 상대 카드 ]                 [ 내 카드 ]", "\n",
            "-" * 64,
            f" 💰 POT: {pot}",
        ])
        if msg: lines.append(f" 📢 {msg}")
        lines.extend([
            "-" * 64,
            f" [ PLAYER ]   칩: {self.p_chip}  |  베팅: {p_bet_amt}",
            "=" * 64,
        ])
        self.print_lines_slow(lines, 0.01)

    # --- 타짜 페이즈 (딜링 & 기술 & 상호 의심) ---
    def tazza_phase(self):
        self.slow_print(f"\n🎲 딜러: [{self.starter}]가 카드를 준비합니다.")
        
        p_card = None
        c_card = None

        # 1. 플레이어가 딜러일 때
        if self.starter == "Player":
            print(f" [1] 정직하게 섞기  [2] 밑장빼기 (성공률 {int(self.CHEAT_SUCCESS_RATE*100)}%)")
            while True:
                choice = input(" 선택 > ")
                if choice in ['1', '2']: break
            
            is_cheating = (choice == '2')
            
            # 섞는 연출
            self.slow_print(" 카드를 섞습니다... 촤르륵...", 0.1)
            
            # [NEW] 컴퓨터의 의심 로직
            # 플레이어가 기술을 쓰면 70% 확률로 의심 (높은 확률로 걸림)
            # 플레이어가 정직하면 10% 확률로 찔러봄 (낮은 확률로 헛다리)
            comp_suspect_prob = 0.7 if is_cheating else 0.1
            
            if random.random() < comp_suspect_prob:
                self.slow_print("\n 🤖 (컴퓨터가 당신의 손을 덮칩니다!)")
                time.sleep(0.5)
                self.slow_print(" 🤖 '동작 그만! 밑장빼기냐?'")
                time.sleep(1)
                
                if is_cheating:
                    self.slow_print(" 😱 걸렸습니다! 소매에서 카드가 떨어집니다...")
                    return None, None, "Player_Caught"
                else:
                    self.slow_print(" 😤 '뭐야? 확인해봐! 난 깨끗해!'")
                    self.slow_print(" 🤖 '...실수했군. 미안하다.'")
                    self.slow_print(" 🎉 컴퓨터가 생사람을 잡았습니다! 위자료 5칩 획득.")
                    self.c_chip -= 5
                    self.p_chip += 5
                    # 정직했으니 정상 진행 (다시 섞기)
                    self.deck.shuffle()
            
            # 의심을 통과했거나, 의심받지 않음
            if is_cheating:
                self.slow_print("\n😎 (컴퓨터가 눈치채지 못했습니다. 기술 성공!)")
                ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
                while True:
                    my_rank = input(f" 내가 가질 카드 ({', '.join(ranks)}) > ").upper()
                    if my_rank in ranks: break
                while True:
                    op_rank = input(" 컴퓨터에게 줄 카드 > ").upper()
                    if op_rank in ranks: break
                
                p_card = self.deck.extract_card(my_rank) or self.deck.draw()
                c_card = self.deck.extract_card(op_rank) or self.deck.draw()
            else:
                self.slow_print(" 정직하게 카드를 섞고 분배합니다.")

        # 2. 컴퓨터가 딜러일 때
        else:
            self.slow_print(" 컴퓨터가 덱을 섞는 중입니다...", 0.1)
            comp_try_cheat = random.random() < (1 - self.CHEAT_SUCCESS_RATE) # 컴퓨터도 비슷하게 시도
            
            print(" 섞는 중... 싹- 싹-")
            time.sleep(1.5)
            print(" 👉 [1] 가만히 있는다  [2] '동작 그만! 밑장빼기냐?' (의심하기)")
            
            while True:
                choice = input(" 선택 > ")
                if choice in ['1', '2']: break
            
            if choice == '2': # 의심하기
                self.slow_print("\n ✋ 동작 그만! 밑장빼기냐?")
                time.sleep(1)
                if comp_try_cheat:
                    self.slow_print(" 🤖 ...쳇, 걸렸군. (증거 확보!)")
                    return None, None, "Computer_Caught"
                else:
                    self.slow_print(" 🤖 '무슨 소리야? 난 정직해!' (증거 없음)")
                    self.slow_print(" 😡 생사람 잡은 벌칙으로 칩 5개를 잃습니다.")
                    self.p_chip -= 5
                    self.c_chip += 5
                    self.deck.shuffle()

            elif choice == '1' and comp_try_cheat:
                # 컴퓨터 기술 성공
                c_card = self.deck.extract_card('A') or self.deck.draw()
                p_card = self.deck.extract_card('2') or self.deck.draw()

        if not p_card: p_card = self.deck.draw()
        if not c_card: c_card = self.deck.draw()
        
        return p_card, c_card, "Normal"

    # --- AI 로직 ---
    def get_computer_action(self, p_card_val, current_bet_diff):
        if p_card_val >= 13:
            if current_bet_diff == 0: return "check"
            if random.random() < 0.8: return "fold"
            return "call"
        elif p_card_val >= 9:
            if current_bet_diff == 0:
                return "bet" if random.random() < 0.3 else "check"
            return "call" if random.random() < 0.6 else "fold"
        else:
            if current_bet_diff == 0: return "bet"
            if random.random() < 0.3: return "raise"
            return "call"

    # --- 베팅 페이즈 ---
    def betting_phase(self, p_card, c_card):
        p_bet = 0; c_bet = 0; pot = 2
        turn = self.starter
        last_action = None
        
        while True:
            self.print_table(p_card, c_card, p_bet, c_bet, pot, msg=f"현재 차례: {turn}")
            
            if turn == "Player":
                to_call = c_bet - p_bet
                if to_call == 0:
                    self.slow_print(" 👉 [1] 체크(Check)  [2] 베팅(Bet)  [3] 폴드(Fold)")
                else:
                    self.slow_print(f" 👉 [1] 콜(Call {to_call}개)  [2] 레이즈(Raise)  [3] 폴드(Fold)")

                while True:
                    c = input(" 선택 > ")
                    if c in ['1','2','3']: break
                
                if c == '3': return "Computer", pot, True # Fold
                elif c == '1':
                    amt = to_call if to_call > 0 else 0
                    if self.p_chip < amt: amt = self.p_chip
                    self.p_chip -= amt; p_bet += amt; pot += amt
                    action = "call" if to_call > 0 else "check"
                    msg = "체크했습니다." if action=="check" else "콜!"
                else:
                    try:
                        amt = int(input(f" 추가 베팅액 (보유:{self.p_chip}) > "))
                    except: amt = 1
                    req = to_call + 1
                    if amt < req: amt = req
                    if amt > self.p_chip: amt = self.p_chip
                    self.p_chip -= amt; p_bet += amt; pot += amt
                    action = "raise"
                    msg = f"{amt}칩 레이즈!"
                
                self.slow_print(f"\n{msg}")
                time.sleep(0.5)
                if (action=="check" and last_action=="check") or (action=="call" and p_bet==c_bet):
                    return "Showdown", pot, False
                last_action = action; turn = "Computer"

            else: # Computer
                to_call = p_bet - c_bet
                act = self.get_computer_action(p_card.value, to_call)
                if act in ['bet','raise'] and self.c_chip <= to_call: act = 'call'
                
                if act == 'fold':
                    self.slow_print("\n🏳️ 컴퓨터 폴드.")
                    return "Player", pot, True
                elif act == 'check':
                    self.slow_print("\n🤖 컴퓨터 체크.")
                    action = 'check'
                elif act == 'call':
                    amt = min(to_call, self.c_chip)
                    self.c_chip -= amt; c_bet += amt; pot += amt
                    self.slow_print(f"\n🤖 컴퓨터 콜 ({amt}칩).")
                    action = 'call'
                else:
                    raise_amt = to_call + random.randint(2,5)
                    if raise_amt > self.c_chip: raise_amt = self.c_chip
                    self.c_chip -= raise_amt; c_bet += raise_amt; pot += raise_amt
                    self.slow_print(f"\n🤖 컴퓨터 레이즈! ({raise_amt}칩)")
                    action = 'raise'
                
                time.sleep(1)
                if (action=="check" and last_action=="check") or (action=="call" and p_bet==c_bet):
                    return "Showdown", pot, False
                last_action = action; turn = "Player"

    def play_round(self):
        if len(self.deck.cards) < 2: self.deck = Deck()
        if self.p_chip < 1 or self.c_chip < 1: return False
        
        self.p_chip -= 1; self.c_chip -= 1
        self.print_rules()

        p_card, c_card, status = self.tazza_phase()

        if status == "Player_Caught":
            self.slow_print("\n🚨 손목이 날아갔습니다... 게임 오버 (당신의 패배)")
            self.p_chip = 0
            return True
        elif status == "Computer_Caught":
            self.slow_print("\n🚨 컴퓨터가 밑장빼기를 하다가 걸렸습니다! (당신의 승리)")
            self.c_chip = 0
            return True

        result, final_pot, folded = self.betting_phase(p_card, c_card)

        if not folded:
            self.print_table(p_card, c_card, 0, 0, final_pot, show_mine=True, msg="Showdown!", clear=False)
            self.slow_print(f"\n[ 나: {p_card} ] vs [ 컴: {c_card} ]")
        
        winner = ""
        if result == "Showdown":
            if p_card > c_card: winner = "Player"
            elif p_card < c_card: winner = "Computer"
            else: winner = "Draw"
        else: winner = result

        if winner == "Player":
            self.slow_print(f"\n🎉 승리! {final_pot}칩 획득.")
            self.p_chip += final_pot; self.starter = "Player"
        elif winner == "Computer":
            self.slow_print(f"\n💀 패배... {final_pot}칩 잃음.")
            self.c_chip += final_pot; self.starter = "Computer"
        else:
            self.slow_print("\n🤝 무승부."); self.p_chip+=final_pot//2; self.c_chip+=final_pot//2

        input("\n[Enter] 다음 라운드...")
        return True

    def run(self):
        while True: # [NEW] 게임 전체 반복 루프
            self.reset_game()
            self.clear_screen()
            self.slow_print("\n🃏 인디언 포커(special edition)")
            time.sleep(1)
            
            while self.p_chip > 0 and self.c_chip > 0:
                if not self.play_round(): break
            
            self.clear_screen()
            if self.p_chip <= 0: print("💔 파산했습니다. 도박 근절 캠페인: 1336")
            else: print("🏆 승리! 축하합니다.")
            
            # [NEW] 재시작 질문
            ask = input("\n🔄 다시 하시겠습니까? (y/n) : ").lower()
            if ask != 'y':
                print("게임을 종료합니다. 이용해 주셔서 감사합니다!")
                break

if __name__ == "__main__":
    game = IndianPokerGame()
    game.run()
