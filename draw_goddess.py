from pathlib import Path

import pygame
from PIL import Image, ImageChops, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "image.png"
OUTPUT = ROOT / "durga_gerua_sketch.png"
WINDOW_SIZE = (900, 900)
PAPER = (250, 247, 238)
GERUA = "#9C4314"
DRAW_SPEED = 18  # horizontal strokes per second


def make_sketch(path: Path, size: tuple[int, int]) -> Image.Image:
    """Make a detailed pencil-shading effect, colored with gerua ink."""
    image = Image.open(path).convert("RGB")
    image.thumbnail(size, Image.Resampling.LANCZOS)

    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            red, green, blue = pixels[x, y]
            if min(red, green, blue) > 224 and max(red, green, blue) - min(red, green, blue) < 15:
                pixels[x, y] = (250, 247, 238)

    gray = ImageOps.autocontrast(ImageOps.grayscale(image), cutoff=1)
   
    edges = gray.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(0.5))
    edge_ink = edges.point(lambda p: min(255, p * 2))
    detailed = ImageOps.autocontrast(ImageChops.subtract(gray, edge_ink), cutoff=1)
    return ImageOps.colorize(detailed, black=GERUA, white="#FFF9EF").convert("RGB")


def main() -> None:
    if not SOURCE.is_file():
        raise FileNotFoundError(f"Put image.png next to this script: {SOURCE}")

    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE, pygame.RESIZABLE)
    pygame.display.set_caption("Gerua sketch — Space: pause, R: restart")
    font = pygame.font.Font(None, 24)
    canvas_size = (960, 960)
    sketch = make_sketch(SOURCE, canvas_size)
    sketch.save(OUTPUT)
    drawing = pygame.image.fromstring(sketch.tobytes(), sketch.size, "RGB")
    paper = pygame.Surface(canvas_size)
    paper.fill(PAPER)

    row = 0.0
    paused = False
    running = True
    clock = pygame.time.Clock()

    while running:
        dt = min(clock.tick(60) / 1000.0, 0.05)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    row = 0.0

        if not paused:
            row = min(float(canvas_size[1]), row + DRAW_SPEED * dt)

        width, height = screen.get_size()
        screen.fill((69, 57, 47))
        margin = 28
        scale = min((width - margin * 2) / canvas_size[0],
                    (height - margin * 2 - 30) / canvas_size[1])
        draw_size = (max(1, int(canvas_size[0] * scale)),
                     max(1, int(canvas_size[1] * scale)))
        left = (width - draw_size[0]) // 2
        top = (height - draw_size[1]) // 2

        sheet = paper.copy()
        completed_rows = int(row)
        if completed_rows:
            rect = pygame.Rect(0, 0, canvas_size[0], completed_rows)
            sheet.blit(drawing, (0, 0), rect)
        scaled = pygame.transform.smoothscale(sheet, draw_size)
        pygame.draw.rect(screen, (38, 31, 27), (left + 7, top + 7, *draw_size), border_radius=2)
        screen.blit(scaled, (left, top))

        if completed_rows < canvas_size[1]:
            progress = row / canvas_size[1]
            pen_x = canvas_size[0] - 1 - int(progress * (canvas_size[0] - 1))
            pen_y = completed_rows
            cursor = (left + int(pen_x * scale), top + int(pen_y * scale))
            pygame.draw.line(screen, (137, 67, 28), cursor,
                             (cursor[0] + 12, cursor[1] - 24), max(2, int(5 * scale)))
            pygame.draw.circle(screen, (240, 185, 111), cursor, max(3, int(4 * scale)))

        percent = int(row * 100 / canvas_size[1])
        status = "Paused" if paused else f"Drawing {percent}%"
        label = font.render(f"{status}    Space: pause    R: restart    Esc: quit", True, (245, 235, 220))
        screen.blit(label, (max(12, (width - label.get_width()) // 2), height - 24))
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
