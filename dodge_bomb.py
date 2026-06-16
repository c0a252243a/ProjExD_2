import os
import sys
import pygame as pg
import time
import random


WIDTH, HEIGHT = 1100, 650
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 移動量の辞書
DELTA = {
    pg.K_UP: (0, -5),     
    pg.K_DOWN: (0, +5),   
    pg.K_LEFT: (-5, 0),    
    pg.K_RIGHT: (+5, 0),   
}

def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内に収まっているか判定する
    引数 obj_rct: 判定対象のRect
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate

def gameover(screen: pg.Surface) -> None:
    """
    ゲームオーバー画面を表示し、5秒間停止する
    引数 screen: メイン画面
    """

    # 画面の暗転
    black_out = pg.Surface((WIDTH, HEIGHT))
    black_out.fill((0, 0, 0))
    black_out.set_alpha(230)

    # テキストの設定
    font = pg.font.Font(None, 80)
    txt_surface = font.render("Game Over", True, (255, 255, 255))
    txt_rect = txt_surface.get_rect()
    txt_rect.center = WIDTH // 2, HEIGHT // 2
    
    # 泣くこうかとんの画像と設定
    cry_kk_img = pg.transform.rotozoom(pg.image.load("fig/8.png"), 0, 0.9)
    cry_kk_rct1 = cry_kk_img.get_rect()
    cry_kk_rct1.center = WIDTH // 2 - 200, HEIGHT // 2
    cry_kk_rct2 = cry_kk_img.get_rect()
    cry_kk_rct2.center = WIDTH // 2 + 200, HEIGHT // 2
    
    # 暗転した画面にテキストと画像を貼り付け
    black_out.blit(txt_surface, txt_rect)
    black_out.blit(cry_kk_img, cry_kk_rct1)
    black_out.blit(cry_kk_img, cry_kk_rct2)
    
    # メイン画面への反映
    screen.blit(black_out, [0, 0])
    pg.display.update()
    time.sleep(5)

def init_bb_imgs() -> tuple[list[pg.Surface], list[int]]:
    """
    10段階のサイズ違いの爆弾と、対応する加速度のリストを生成する
    """
    bb_imgs = []

    #爆弾を生成
    for r in range(1, 11):
        bb_img = pg.Surface((20 * r, 20 * r)) 
        bb_img.fill((0, 0, 0)) 
        pg.draw.circle(bb_img, (255, 0, 0), (10 * r, 10 * r), 10 * r)
        bb_img.set_colorkey((0, 0, 0)) 
        bb_imgs.append(bb_img)
    
    bb_accs = [a for a in range(1, 11)]   # 加速度 [1~10] 
    return bb_imgs, bb_accs

def calc_orientation(org: pg.Rect, dst: pg.Rect, current_xy: tuple[float, float]) -> tuple[float, float]:
    """
    爆弾から終点こうかとんへの方向ベクトルを計算する
    引数 org: 爆弾のRect
    引数 dst: こうかとんのRect
    引数 current_xy: 計算前の方向ベクトル (vx, vy)
    戻り値: タプル (正規化後の方向ベクトル、または計算前の方向ベクトル)
    """
    # orgとdstの座標ベクトル間の差ベクトルを求める
    dx = dst.centerx - org.centerx
    dy = dst.centery - org.centery
    
    # 正規化前の差ベクトルのノルム（距離）を計算
    dist = (dx**2 + dy**2) ** 0.5
    
    # 爆弾とこうかとんの距離が300未満だったら、慣性として計算前の方向を返す
    if dist < 300:
        return current_xy
        
    # 差ベクトルのノルムが√50になるように正規化する
    if dist != 0:
        norm = 50 ** 0.5  # √50
        vx = norm * dx / dist
        vy = norm * dy / dist
        return vx, vy
        
    return current_xy

def main():
    """ゲームのメインループ処理"""

    pg.display.set_caption("逃げろ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")

    # こうかとんの初期化（方向を切り替えるための辞書）
    kk_img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9) 
    kk_img1 = pg.transform.flip(kk_img0, True, False) 
    kk_imgs = {
        (0, 0): kk_img0,
        (-5, 0): kk_img0,
        (-5, -5): pg.transform.rotozoom(kk_img0, -45, 1.0),
        (0, -5): pg.transform.rotozoom(kk_img1, 90, 1.0),
        (+5, -5): pg.transform.rotozoom(kk_img1, 45, 1.0), 
        (+5, 0): kk_img1, 
        (+5, +5): pg.transform.rotozoom(kk_img1, -45, 1.0),
        (0, +5): pg.transform.rotozoom(kk_img1, -90, 1.0),
        (-5, +5): pg.transform.rotozoom(kk_img0, 45, 1.0),
    }
    kk_img = kk_imgs[(0, 0)]
    kk_rct = kk_img.get_rect()
    kk_rct.center = 300, 200

    # 制御するためのタイマー
    clock = pg.time.Clock()
    tmr = 0

    # 爆弾の初期化
    bb_imgs, bb_accs = init_bb_imgs()
    bb_img = bb_imgs[0]
    bb_rct = bb_img.get_rect()
    bb_rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
    vx, vy = +5, +5

    # メインのループ
    while True:
        # イベントの確認
        for event in pg.event.get():
            if event.type == pg.QUIT: 
                return
        screen.blit(bg_img, [0, 0]) 

        # 移動の処理
        key_lst = pg.key.get_pressed()
        sum_mv = [0, 0]
        for key, delta in DELTA.items():
            if key_lst[key]: 
                sum_mv[0] += delta[0]
                sum_mv[1] += delta[1]
        kk_rct.move_ip(sum_mv)

        # 壁に衝突したかを判定
        yoko, tate = check_bound(kk_rct)
        if not yoko or not tate:
            kk_rct.move_ip(-sum_mv[0], -sum_mv[1])

        # 移動方向に応じた画像へ切り替えて描画
        kk_img = kk_imgs[tuple(sum_mv)]
        screen.blit(kk_img, kk_rct)

        # 時間に応じて爆弾のサイズを更新
        idx = min(tmr // 500, 9)
        bb_img = bb_imgs[idx]
        bb_rct.width = bb_img.get_rect().width
        bb_rct.height = bb_img.get_rect().height
        
        # 追従する速度の計算
        vx, vy = calc_orientation(bb_rct, kk_rct, (vx, vy))

        # 加速度を用いて爆弾を移動
        avx = vx * bb_accs[idx]
        avy = vy * bb_accs[idx]
        bb_rct.move_ip(avx, avy)
        screen.blit(bb_img, bb_rct)

        # 衝突したらgameover関数を呼び出して終了
        if kk_rct.colliderect(bb_rct):
            gameover(screen)
            return
        
        # 画面の更新とフレームレートの維持
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()