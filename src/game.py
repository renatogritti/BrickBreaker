import pygame
import numpy as np
import random
from src.settings import *
from src.sprites import Paddle, Ball, Brick

class Game:
    """
    Gerencia a lógica principal do jogo Brick Breaker, incluindo inicialização,
    loops de jogo, gerenciamento de eventos, atualizações de estado e renderização.
    """

    def __init__(self):
        """
        Inicializa o Pygame, configura a tela, carrega sons e define os estados iniciais do jogo.
        """
        pygame.init()
        pygame.mixer.init() # Inicializa o mixer para sons
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Brick Breaker")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.running = True
        self.game_over = False
        self.game_won = False # Novo estado para vitória
        self.level_complete = False # Novo estado para fase concluída
        self.generate_bip_sounds() # Gera os sons de bip

        # Inicializa grupos de sprites e objetos aqui
        self.all_sprites = pygame.sprite.Group()
        self.bricks = pygame.sprite.Group()
        self.balls = pygame.sprite.Group()
        self.paddle = Paddle()
        self.ball = Ball() # A bola inicial
        self.all_sprites.add(self.paddle)
        
        self.reset_game()

    def generate_bip_sounds(self):
        """
        Gera e carrega os sons de "bip" para diferentes eventos do jogo (colisões, perda de vida, etc.)
        usando a biblioteca numpy para criar as ondas sonoras.
        """
        # Frequências e durações para os bips
        freq_brick = 440  # A4
        freq_paddle = 660 # E5
        freq_wall = 880   # A5
        freq_lose_life = 220 # A3
        freq_victory = 1320 # E6
        freq_level_complete = 1000 # C6
        duration = 0.05 # segundos

        sample_rate = pygame.mixer.get_init()[0] # Obtém a taxa de amostragem do mixer

        def create_bip(frequency, duration_sec):
            """
            Cria um som de bip com a frequência e duração especificadas.
            Args:
                frequency (int): A frequência do som em Hz.
                duration_sec (float): A duração do som em segundos.
            Returns:
                pygame.mixer.Sound: O objeto Sound gerado.
            """
            num_samples = int(sample_rate * duration_sec)
            arr = np.sin(2 * np.pi * frequency * np.arange(num_samples) / sample_rate).astype(np.float32)
            # Reshape para 2D para mixer estéreo (mesmo que seja mono)
            arr = np.array([arr, arr]).T # Para estéreo, duplica e transpõe
            arr = np.ascontiguousarray(arr) # Garante que o array seja C-contiguous
            sound = pygame.sndarray.make_sound(arr)
            return sound

        self.sound_brick_hit = create_bip(freq_brick, duration)
        self.sound_paddle_hit = create_bip(freq_paddle, duration)
        self.sound_wall_hit = create_bip(freq_wall, duration)
        self.sound_lose_life = create_bip(freq_lose_life, duration * 2) # Um pouco mais longo
        self.sound_victory = create_bip(freq_victory, duration * 3) # Mais longo para vitória
        self.sound_level_complete = create_bip(freq_level_complete, duration * 2) # Som para fase concluída

    def reset_game(self):
        """
        Reinicia o jogo para o estado inicial, resetando pontuação, vidas, nível e recriando os elementos do jogo.
        """
        self.game_over = False
        self.game_won = False
        self.level_complete = False # Resetar também ao reiniciar o jogo
        self.score = 0
        self.lives = 3
        self.level = 1
        
        # Limpa os grupos existentes
        self.all_sprites.empty()
        self.bricks.empty()
        self.balls.empty()

        # Recria a raquete e a bola inicial
        self.paddle = Paddle()
        self.ball = Ball()
        self.all_sprites.add(self.paddle, self.ball)
        self.balls.add(self.ball)
        
        self.create_bricks()
        self.reset_ball()

    def reset_ball(self):
        """
        Reinicia a posição e velocidade da bola, centralizando-a na raquete e ajustando a velocidade
        com base no nível atual.
        """
        # Remove todas as bolas existentes
        for ball in self.balls:
            ball.kill()
        self.balls.empty()

        # Cria uma nova bola
        self.ball = Ball()
        self.all_sprites.add(self.ball)
        self.balls.add(self.ball)

        self.ball_launched = False
        self.ball.rect.centerx = self.paddle.rect.centerx
        self.ball.rect.bottom = self.paddle.rect.top
        self.ball.speed_x = BALL_SPEED_X + (self.level - 1)
        self.ball.speed_y = -(BALL_SPEED_Y + (self.level - 1))

    def create_bricks(self):
        """
        Cria os tijolos para o nível atual, incluindo tijolos especiais a partir do nível 2.
        """
        self.bricks.empty()
        for sprite in self.all_sprites:
            if isinstance(sprite, Brick):
                sprite.kill()

        colors = [RED, GREEN, BLUE]
        for i in range(5):
            for j in range(10):
                is_special = False
                if self.level >= 2 and random.random() < 0.1: # 10% de chance de ser especial a partir do nível 2
                    is_special = True
                brick = Brick(j * (60 + 10) + 35, i * (20 + 10) + 50, colors[i % len(colors)], is_special=is_special)
                self.all_sprites.add(brick)
                self.bricks.add(brick)

    def run(self):
        """
        Inicia o loop principal do jogo, que inclui a splash screen, o loop de eventos,
        atualização do estado do jogo e renderização.
        """
        # Loop da Splash Screen
        splash_screen_active = True
        while splash_screen_active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    splash_screen_active = False
                if event.type == pygame.KEYDOWN:
                    splash_screen_active = False
            self.draw_splash_screen()
            pygame.display.flip()
            self.clock.tick(FPS)

        # Loop principal do jogo
        while self.running:
            self.clock.tick(FPS)
            self.events()
            self.update()
            self.draw()
        pygame.quit()

    def events(self):
        """
        Processa os eventos do Pygame, como fechar a janela, pressionar teclas para reiniciar ou sair,
        e lançar a bola.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if self.game_over or self.game_won or self.level_complete: # Lida com eventos na tela de fim de jogo/vitória/fase concluída
                    if event.key == pygame.K_r:
                        self.reset_game()
                    if event.key == pygame.K_q:
                        self.running = False
                else:
                    if event.key == pygame.K_SPACE and not self.ball_launched:
                        self.ball_launched = True

    def update(self):
        """
        Atualiza o estado de todos os elementos do jogo, como a posição da raquete e da bola,
        e verifica colisões.
        """
        if self.game_over or self.game_won or self.level_complete:
            return

        self.paddle.update()

        if self.ball_launched:
            for ball in self.balls:
                ball.update()
                self.check_collisions(ball) # Passa a bola atual como argumento
        else:
            self.ball.rect.centerx = self.paddle.rect.centerx
            self.ball.rect.bottom = self.paddle.rect.top

    def check_collisions(self, ball):
        """
        Verifica e lida com todas as colisões da bola com as paredes, raquete e tijolos.
        Args:
            ball (Ball): O objeto Ball a ser verificado para colisões.
        """
        if ball.rect.left <= 0 or ball.rect.right >= SCREEN_WIDTH:
            ball.speed_x *= -1
            self.sound_wall_hit.play()
        if ball.rect.top <= 0:
            ball.speed_y *= -1
            self.sound_wall_hit.play()

        if pygame.sprite.collide_rect(ball, self.paddle):
            ball.speed_y *= -1
            ball.rect.bottom = self.paddle.rect.top
            self.sound_paddle_hit.play()

        hits = pygame.sprite.spritecollide(ball, self.bricks, True)
        if hits:
            self.score += 10
            ball.speed_y *= -1
            self.sound_brick_hit.play()
            for hit_brick in hits:
                if hit_brick.is_special:
                    new_ball = Ball()
                    new_ball.rect.center = hit_brick.rect.center
                    new_ball.speed_x = random.choice([-BALL_SPEED_X, BALL_SPEED_X])
                    new_ball.speed_y = -BALL_SPEED_Y
                    self.all_sprites.add(new_ball)
                    self.balls.add(new_ball)

        if not self.bricks:
            self.level_complete = True
            self.sound_level_complete.play()
            pygame.time.wait(2000) # 2 segundos de pausa
            
            self.level += 1
            if self.level > 3: # Condição de vitória: 3 níveis completos
                self.game_won = True
                self.sound_victory.play()
            else:
                self.create_bricks()
                self.reset_ball()
            self.level_complete = False # Reseta o estado após a transição

        # Se a bola atinge a parte inferior da tela
        if ball.rect.top > SCREEN_HEIGHT:
            ball.kill() # Remove a bola que caiu
            if not self.balls: # Se não houver mais bolas em jogo
                self.lives -= 1
                self.sound_lose_life.play()
                if self.lives > 0:
                    self.reset_ball()
                else:
                    self.lives = 0
                    self.game_over = True

    def draw(self):
        """
        Desenha todos os elementos do jogo na tela, incluindo sprites, HUD e telas de estado do jogo.
        """
        self.screen.fill(BLACK)
        self.all_sprites.draw(self.screen)
        self.balls.draw(self.screen) # Desenha todas as bolas
        
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        lives_text = self.font.render(f"Lives: {self.lives}", True, WHITE)
        level_text = self.font.render(f"Level: {self.level}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        self.screen.blit(lives_text, (SCREEN_WIDTH - 120, 10))
        self.screen.blit(level_text, (SCREEN_WIDTH // 2 - 50, 10))

        if self.game_over:
            self.draw_game_over()
        elif self.game_won: # Desenha tela de vitória
            self.draw_game_won()
        elif self.level_complete: # Desenha tela de fase concluída
            self.draw_level_complete()

        pygame.display.flip()

    def draw_game_over(self):
        """
        Desenha a tela de "Game Over" com a pontuação final e opções para reiniciar ou sair.
        """
        game_over_font = pygame.font.Font(None, 72)
        restart_font = pygame.font.Font(None, 36)
        
        game_over_text = game_over_font.render("GAME OVER", True, RED)
        score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
        restart_text = restart_font.render("Pressione R para reiniciar ou Q para sair", True, WHITE)
        
        self.screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 2 - 100))
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 100))

    def draw_game_won(self):
        """
        Desenha a tela de "Você Venceu!" com a pontuação final e opções para reiniciar ou sair.
        """
        game_won_font = pygame.font.Font(None, 72)
        restart_font = pygame.font.Font(None, 36)

        game_won_text = game_won_font.render("VOCÊ VENCEU!", True, GREEN)
        score_text = self.font.render(f"Pontuação Final: {self.score}", True, WHITE)
        restart_text = restart_font.render("Pressione R para reiniciar ou Q para sair", True, WHITE)

        self.screen.blit(game_won_text, (SCREEN_WIDTH // 2 - game_won_text.get_width() // 2, SCREEN_HEIGHT // 2 - 100))
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 100))

    def draw_level_complete(self):
        """
        Desenha a tela de "Fase Concluída!" ao final de cada nível.
        """
        level_complete_font = pygame.font.Font(None, 72)
        level_complete_text = level_complete_font.render(f"FASE {self.level - 1} CONCLUÍDA!", True, GREEN)
        self.screen.blit(level_complete_text, (SCREEN_WIDTH // 2 - level_complete_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))

    def draw_splash_screen(self):
        """
        Desenha a tela de introdução (splash screen) do jogo.
        """
        self.screen.fill(BLACK)
        title_font = pygame.font.Font(None, 100)
        press_key_font = pygame.font.Font(None, 50)

        title_text = title_font.render("BRICK BREAKER", True, WHITE)
        press_key_text = press_key_font.render("Pressione qualquer tecla para iniciar", True, WHITE)

        self.screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, SCREEN_HEIGHT // 2 - 100))
        self.screen.blit(press_key_text, (SCREEN_WIDTH // 2 - press_key_text.get_width() // 2, SCREEN_HEIGHT // 2 + 50))