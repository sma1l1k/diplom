import pygame
import sys
import math

from pygame.locals import *
from pygame.color import THECOLORS

from Vec2D import Vec2D

class Client:
    def __init__(self, cursor_color):
        self.cursor_location_in_pixels = (0,0)   # x_in_pixels, y_in_pixels
        self.mouse_button = 1             # 1, 2, or 3
        self.buttonIsStillDown = False

        # Freeze it
        self.key_f = "U"

        # Zoom
        self.key_b = "U"
        self.key_n = "U"
        self.key_m = "U"
        self.key_h = "U"

        self.selected_particle = None
        self.cursor_color = cursor_color
        self.Qcount = 0
        self.bullet_hit_count = 0
        self.bullet_hit_limit = 150.0

        # Определение характера строк курсора, по одной для каждой кнопки мыши.
        self.mouse_strings = {'string1':{'c_drag':   2.0, 'k_Npm':   60.0},
                              'string2':{'c_drag':   0.2, 'k_Npm':    2.0},
                              'string3':{'c_drag':  20.0, 'k_Npm': 1000.0}}

    def calc_string_forces_on_particles(self):
        # Вычисление струнных сил на выбранную частицу и добавления совокупности,
        # которая хранится в объекте частицы.

        # Проверка только выбранной частицы, если она ещё не выбрана. Это удерживает частицу
        # от смены выбора, если курсор перетащен с частцы
        if (self.selected_particle == None):
            if self.buttonIsStillDown:
                self.selected_particle = space.checkForParticleAtThisPosition(self.cursor_location_in_pixels)

        else:
            if not self.buttonIsStillDown:
                self.selected_particle.selected = False
                self.selected_particle = None
                return None

            # Используйте разницу в dx для расчета силы  зацепки, применяемой линией привязи.
            # Если вы отпустите кнопку мыши после перетаскивания, она будет швырять частицу.
            # Эта сила привязи будет уменьшаться, когда частица приближается к точке мыши.
            dx_in_meters = nature.ConvertScreenToWorld(Vec2D(self.cursor_location_in_pixels)) - self.selected_particle.position_in_meters

            stringName = "string" + str(self.mouse_button)
            self.selected_particle.cursorString_spring_force_2d_N   += dx_in_meters * self.mouse_strings[stringName]['k_Npm']
            self.selected_particle.cursorString_particleDrag_force_2d_N += (self.selected_particle.velocity *
                                                                    -1 * self.mouse_strings[stringName]['c_drag'])

    def draw_cursor_string(self):
        line_points = [nature.ConvertWorldToScreen(self.selected_particle.position_in_meters), self.cursor_location_in_pixels]
        if (self.selected_particle != None):
            pygame.draw.line(surface_window.surface, self.cursor_color, line_points[0], line_points[1], 1)

class GameWindow:
    def __init__(self, screen, screen_title):
        self.screen_width = screen[0]
        self.screen_height = screen[1]
        self.UpperRight = nature.ConvertScreenToWorld(Vec2D(self.screen_width, 0))
        self.surface = pygame.display.set_mode(screen)

        self.update_caption(screen_title)

        self.surface.fill(THECOLORS["black"])
        pygame.display.update()

    def update_caption(self, screen_title):
        pygame.display.set_caption( screen_title)

    def update(self):
        pygame.display.update()

    def clear(self):
        self.surface.fill(THECOLORS["black"])
        pygame.display.update()

class Space:
    def __init__(self, walls_dic):
        self.gON_mps2 = Vec2D(-0.0, -9.0)
        self.gOFF_mps2 = Vec2D(-0.0, -0.0)
        self.g_2d_mps2 = self.gOFF_mps2
        self.g_ON = False
        self.particles = []
        self.controlled_particles = []
        self.springs = []
        self.walls = walls_dic
        self.collision_count = 0
        self.coef_rest_particle =  0.90
        self.coef_rest_table = 0.90
        self.color_transfer = False

    def draw(self):
        topLeft_in_pixels =   nature.ConvertWorldToScreen( Vec2D( self.walls['L_m'],        self.walls['T_m']))
        topRight_in_pixels =  nature.ConvertWorldToScreen( Vec2D( self.walls['R_m']-0.01,   self.walls['T_m']))
        botLeft_in_pixels =   nature.ConvertWorldToScreen( Vec2D( self.walls['L_m'],        self.walls['B_m']+0.01))
        botRight_in_pixels =  nature.ConvertWorldToScreen( Vec2D( self.walls['R_m']-0.01,   self.walls['B_m']+0.01))

        pygame.draw.line(surface_window.surface, THECOLORS["orangered1"], topLeft_in_pixels,  topRight_in_pixels, 1)
        pygame.draw.line(surface_window.surface, THECOLORS["orangered1"], topRight_in_pixels, botRight_in_pixels, 1)
        pygame.draw.line(surface_window.surface, THECOLORS["orangered1"], botRight_in_pixels, botLeft_in_pixels,  1)
        pygame.draw.line(surface_window.surface, THECOLORS["orangered1"], botLeft_in_pixels,  topLeft_in_pixels,  1)

    def checkForParticleAtThisPosition(self, x_in_pixels_or_tuple, y_in_pixels = None):
        if y_in_pixels == None:
            self.x_in_pixels = x_in_pixels_or_tuple[0]
            self.y_in_pixels = x_in_pixels_or_tuple[1]
        else:
            self.x_in_pixels = x_in_pixels_or_tuple
            self.y_in_pixels = y_in_pixels

        test_position_m = nature.ConvertScreenToWorld(Vec2D(self.x_in_pixels, self.y_in_pixels))
        for particle in self.particles:
            vector_difference_m = test_position_m - particle.position_in_meters
            # Используется квадрат длины для скорости(избегаем квадратного корня)
            mag_of_difference_m2 = vector_difference_m.length_squared()
            if mag_of_difference_m2 < particle.r_in_meters**2:
                particle.selected = True
                return particle
        return None

    def update_particleSpeedAndPosition(self, particle, dt_s):
        # Чистая результирующая сила на частицу.
        particle_forces_2d_N = (self.g_2d_mps2 * particle.mass) + (particle.SprDamp_force_2d_N +
                                                              particle.jet_force_2d_N +
                                                              particle.cursorString_spring_force_2d_N +
                                                              particle.cursorString_particleDrag_force_2d_N +
                                                              particle.impulse/dt_s)

        # Ускорение, по закону Ньютона.
        acceleration = particle_forces_2d_N / particle.mass

        # Изменение скорости:  dv = a * dt
        # Скорость в конце отметки времени.
        particle.velocity = particle.velocity + (acceleration * dt_s)

        # Рассчитывание новой физической позиции частицы, используя скорость в конце отметки времени.
        # Изменение позиции с помощью скорости:  dx = v * dt
        particle.position_in_meters = particle.position_in_meters + (particle.velocity * dt_s)

        # Сбрасывание совокупности силы.
        particle.SprDamp_force_2d_N = Vec2D(0.0,0.0)
        particle.cursorString_spring_force_2d_N = Vec2D(0.0,0.0)
        particle.cursorString_particleDrag_force_2d_N = Vec2D(0.0,0.0)
        particle.impulse = Vec2D(0.0,0.0)

    def check_for_collisions(self):
        for i, particle in enumerate(self.particles):

            # Проверка верхней, нижней стенки.
            if (((particle.position_in_meters.y - particle.r_in_meters) < self.walls["B_m"]) or ((particle.position_in_meters.y + particle.r_in_meters) > self.walls["T_m"])):

                if self.correct_for_wall_penetration:
                    if (particle.position_in_meters.y - particle.r_in_meters) < self.walls["B_m"]:
                        penetration_y_in_meters = self.walls["B_m"] - (particle.position_in_meters.y - particle.r_in_meters)
                        particle.position_in_meters.y += 2 * penetration_y_in_meters

                    if (particle.position_in_meters.y + particle.r_in_meters) > self.walls["T_m"]:
                        penetration_y_in_meters = (particle.position_in_meters.y + particle.r_in_meters) - self.walls["T_m"]
                        particle.position_in_meters.y -= 2 * penetration_y_in_meters

                particle.velocity.y *= -1 * self.coef_rest_table

            # Проверка боковых стенок.
            if (((particle.position_in_meters.x - particle.r_in_meters) < self.walls["L_m"]) or ((particle.position_in_meters.x + particle.r_in_meters) > self.walls["R_m"])):

                if self.correct_for_wall_penetration:
                    if (particle.position_in_meters.x - particle.r_in_meters) < self.walls["L_m"]:
                        penetration_x_in_meters = self.walls["L_m"] - (particle.position_in_meters.x - particle.r_in_meters)
                        particle.position_in_meters.x += 2 * penetration_x_in_meters

                    if (particle.position_in_meters.x + particle.r_in_meters) > self.walls["R_m"]:
                        penetration_x_in_meters = (particle.position_in_meters.x + particle.r_in_meters) - self.walls["R_m"]
                        particle.position_in_meters.x -= 2 * penetration_x_in_meters

                particle.velocity.x *= -1 * self.coef_rest_table

            # Столкновение с другими частицами.
            for otherparticle in self.particles[i+1:]:

                # Проверка на прикрывание частиц друг с другом.

                # Параллельно нормальному
                particle_to_particle_in_meters = otherparticle.position_in_meters - particle.position_in_meters
                # ПАралелльно касательной
                tanget_p_to_p_in_meters = Vec2D.rotate90(particle_to_particle_in_meters)

                p_to_p_in_meters2 = particle_to_particle_in_meters.length_squared()

                # Проверка быстрее, если избегать квадратных корней
                if (p_to_p_in_meters2 < (particle.r_in_meters + otherparticle.r_in_meters)**2):
                    self.collision_count += 1

                    # Используется ветор p_to_p(между двумя сталкивающимися частицами) в качестве цели проекции
                    # для нормального расчета

                    # Вычислить компоненты скорости вдоль и перпендикулярно нормали.
                    particle_normal = particle.velocity.projection_onto(particle_to_particle_in_meters)
                    particle_tangent = particle.velocity.projection_onto(tanget_p_to_p_in_meters)

                    otherparticle_normal = otherparticle.velocity.projection_onto(particle_to_particle_in_meters)
                    otherparticle_tangent = otherparticle.velocity.projection_onto(tanget_p_to_p_in_meters)

                    relative_normal_velocity = otherparticle_normal - particle_normal

                    if self.correct_for_particle_penetration:
                        # Отступы в общей сложности 2х проникновений по нормали. Количество отступов для каждой частицы
                        # зависит от скорости каждой частицы 2DT, где DT - время проникновения. DT рассчитывается
                        # из относительной скорости и расстояния проникновения.

                        relative_normal_spd_mps = relative_normal_velocity.length()
                        penetration_m = (particle.r_in_meters + otherparticle.r_in_meters) - p_to_p_in_meters2**0.5
                        if (relative_normal_spd_mps > 0.00001):
                            penetration_time_s = penetration_m / relative_normal_spd_mps

                            penetration_time_scaler = 1.0  # Это может быть полезно для тестирования, чтобы усилить и увидеть коррецию.

                            # Сначала перевенуть две щайбы к точке их столкновения по траектории их входящей траектории.
                            particle.position_in_meters = particle.position_in_meters - (particle_normal * (penetration_time_scaler * penetration_time_s))
                            otherparticle.position_in_meters = otherparticle.position_in_meters - (otherparticle_normal * (penetration_time_scaler * penetration_time_s))

                            # Рассчитывание скорости по нормали ПОСЛЕ столкновения. Используется CR(коэффициент возвращения)
                            # лучше всего 1, чтобы избежать липкости.
                            CR_particle = 1
                            particle_normal_AFTER_mps, otherparticle_normal_AFTER_mps = self.AandB_normal_AFTER_Calculation( particle_normal, particle.mass, otherparticle_normal, otherparticle.mass, CR_particle)

                            # Наконец, пройти ещё один раз по величине времени проникновения, используя эти скорости ПОСЛЕ столкновения.
                            # Это поместит частицу туда, где она должна бы была быть в момент столкновения.
                            particle.position_in_meters = particle.position_in_meters + (particle_normal_AFTER_mps * (penetration_time_scaler * penetration_time_s))
                            otherparticle.position_in_meters = otherparticle.position_in_meters + (otherparticle_normal_AFTER_mps * (penetration_time_scaler * penetration_time_s))

                        else:
                            pass

                    # Присвоить скорости ПОСЛЕ (используя фактический CR) частице для использования в следуюзем расчете кадра.
                    CR_particle = self.coef_rest_particle
                    particle_normal_AFTER_mps, otherparticle_normal_AFTER_mps = self.AandB_normal_AFTER_Calculation( particle_normal, particle.mass, otherparticle_normal, otherparticle.mass, CR_particle)

                    # Теперь, когда закончили использовать текущие значения, установите их для вновь рассчитанных AFTER.
                    particle_normal, otherparticle_normal = particle_normal_AFTER_mps, otherparticle_normal_AFTER_mps

                    # Сложение компонентов, чтобы получить векторы общей скорости для каждой частицы.
                    particle.velocity = particle_normal + particle_tangent
                    otherparticle.velocity = otherparticle_normal + otherparticle_tangent

    def normal_AFTER_Calculation(self, A_normal_BEFORE, A_mass, B_normal_BEFORE, B_mass, CR_particle):
        # Для входов, как определено здесь, это возвращает нормальное значение AFTER для первой частицы на входах.
        # Таким образом, если B является первым, он возвращает результат для B частцы.
        relative_normal_velocity = B_normal_BEFORE - A_normal_BEFORE
        return ( ( (relative_normal_velocity * (CR_particle * B_mass)) +
                   (A_normal_BEFORE * A_mass + B_normal_BEFORE * B_mass) ) /
                   (A_mass + B_mass) )

    def AandB_normal_AFTER_Calculation(self, A_normal_BEFORE, A_mass, B_normal_BEFORE, B_mass, CR_particle):
        A = self.normal_AFTER_Calculation(A_normal_BEFORE, A_mass, B_normal_BEFORE, B_mass, CR_particle)
        # Используется симметрия в физике, чтобы вычислить нормаль B(поместить данные B в первые входы).
        B = self.normal_AFTER_Calculation(B_normal_BEFORE, B_mass, A_normal_BEFORE, A_mass, CR_particle)
        return A, B

class Environment:
    def __init__(self, screenSize_in_pixels, length_x_in_meters):
        self.screenSize_in_pixels = Vec2D(screenSize_in_pixels)
        self.viewOffset_in_pixels = Vec2D(0,0)
        self.viewCenter_in_pixels = Vec2D(0,0)
        self.viewZoom = 1
        self.viewZoom_rate = 0.01
        self.time_s = 0

        self.clients = {'local':Client(THECOLORS["green"])}

        self.pixels_to_meters = length_x_in_meters/float(self.screenSize_in_pixels.x)
        self.meters_to_pixels = (float(self.screenSize_in_pixels.x)/length_x_in_meters)

    def pixels_from_meters(self, dx_in_meters):
        return dx_in_meters * self.meters_to_pixels * self.viewZoom

    def meters_from_pixels(self, dx_in_pixels):
        return float(dx_in_pixels) * self.pixels_to_meters / self.viewZoom

    def ConvertScreenToWorld(self, point_in_pixels):
        x_in_meters = (point_in_pixels.x + self.viewOffset_in_pixels.x) / (self.meters_to_pixels * self.viewZoom)
        y_in_meters = (self.screenSize_in_pixels.y - point_in_pixels.y + self.viewOffset_in_pixels.y) / (self.meters_to_pixels * self.viewZoom)
        return Vec2D( x_in_meters, y_in_meters)

    def ConvertWorldToScreen(self, point_in_meters):
        x_in_pixels = (point_in_meters.x * self.meters_to_pixels * self.viewZoom) - self.viewOffset_in_pixels.x
        y_in_pixels = (point_in_meters.y * self.meters_to_pixels * self.viewZoom) - self.viewOffset_in_pixels.y
        y_in_pixels = self.screenSize_in_pixels.y - y_in_pixels

        return Vec2D(x_in_pixels, y_in_pixels, "int").tuple()

    def get_local_user_input(self):
        local_user = self.clients['local']

        # Get all the events since the last call to get().
        for event in pygame.event.get():
            if (event.type == pygame.QUIT):
                sys.exit()
            elif (event.type == pygame.KEYDOWN):
                if (event.key == K_ESCAPE):
                    sys.exit()
                elif (event.key==K_1):
                    return 1
                elif (event.key==K_2):
                    return 2
                elif (event.key==K_3):
                    return 3
                elif (event.key==K_4):
                    return 4
                elif (event.key==K_5):
                    return 5
                elif (event.key==K_6):
                    return 6
                elif (event.key==K_7):
                    return 7
                elif (event.key==K_8):
                    return 8
                elif (event.key==K_9):
                    return 9
                elif (event.key==K_0):
                    return 0

                elif (event.key==K_c):
                    # Toggle color option.
                    space.color_transfer = not space.color_transfer

                elif (event.key==K_f):
                    for Particle in space.particles:
                        Particle.velocity = Vec2D(0,0)

                elif (event.key==K_g):
                    if space.g_ON:
                        space.g_2d_mps2 = space.gOFF_mps2
                        space.coef_rest_Particle =  1.00
                        space.coef_rest_table =  1.00
                    else:
                        space.g_2d_mps2 = space.gON_mps2
                        space.coef_rest_Particle =  0.90
                        space.coef_rest_table =  0.90
                    space.g_ON = not space.g_ON
                    print("g", space.g_ON)

                elif (event.key==K_F2):
                    # Toggle menu on/off
                    pass

                # Zoom keys
                elif (event.key==K_b):
                    local_user.key_b = 'D'
                elif (event.key==K_n):
                    local_user.key_n = 'D'
                elif (event.key==K_m):
                    local_user.m = 'D'
                elif (event.key==K_h):
                    local_user.key_h = 'D'

                # Penetration correction
                elif (event.key==K_p):
                    space.correct_for_particle_penetration = not space.correct_for_particle_penetration

                else:
                    return "nothing set up for this key"

            elif (event.type == pygame.KEYUP):
                # Zoom keys
                if (event.key==K_b):
                    local_user.key_b = 'U'
                elif (event.key==K_n):
                    local_user.key_n = 'U'
                elif (event.key==K_m):
                    local_user.key_m = 'U'
                elif (event.key==K_h):
                    local_user.key_h = 'U'

            elif event.type == pygame.MOUSEBUTTONDOWN:
                local_user.buttonIsStillDown = True

                (button1, button2, button3) = pygame.mouse.get_pressed()
                if button1:
                    local_user.mouse_button = 1
                elif button2:
                    local_user.mouse_button = 2
                elif button3:
                    local_user.mouse_button = 3
                else:
                    local_user.mouse_button = 0

            elif event.type == pygame.MOUSEBUTTONUP:
                local_user.buttonIsStillDown = False
                local_user.mouse_button = 0

            # In all cases, pass the event to the Gui.
            #app.event(event)

        if local_user.buttonIsStillDown:
            # This will select a Particle when the Particle runs into the cursor of the mouse with it's button still down.
            local_user.cursor_location_in_pixels = (mouseX, mouseY) = pygame.mouse.get_pos()

class Particle:
    def __init__(self, position_in_meters, r_in_meters, particle_density, particle_color = THECOLORS["grey"]):
        self.r_in_meters = r_in_meters
        self.r_in_px = int(round(nature.pixels_from_meters(self.r_in_meters * nature.viewZoom)))
        self.particle_density = particle_density    # масса на единицу площади
        self.mass = self.particle_density * math.pi * self.r_in_meters ** 2
        self.position_in_meters = position_in_meters
        self.velocity = Vec2D(0.0,0.0)
        self.SprDamp_force_2d_N = Vec2D(0.0,0.0)
        self.jet_force_2d_N = Vec2D(0.0,0.0)
        self.cursorString_spring_force_2d_N = Vec2D(0.0,0.0)
        self.cursorString_particleDrag_force_2d_N = Vec2D(0.0,0.0)
        self.impulse = Vec2D(0.0,0.0)
        self.color = particle_color

    # Для вывод координат нахождения частицы
    def __str__(self):
        return "particle: x is %s, y is %s" % (self.position_in_meters.x, self.position_in_meters.y)

    def draw(self):
        # Преобразование x, y из метров в реальном представлении в пиксели
        self.position_in_px = nature.ConvertWorldToScreen( self.position_in_meters)

        # Обновлять на основе увеличения
        self.r_in_px = int(round(nature.pixels_from_meters( self.r_in_meters)))
        if (self.r_in_px < 3):
            self.r_in_px = 3
        particle_thickness = 3
        particle_color = self.color
        # Рисовать саму частицу
        pygame.draw.circle(surface_window.surface, particle_color, self.position_in_px, self.r_in_px, particle_thickness)

class Spring:
    def __init__(self, particle1, particle2, length_in_meters=3.0, strength_Npm=0.5, spring_color=THECOLORS["yellow"], width_in_meters=0.025):
        self.particle1 = particle1
        self.particle2 = particle2
        self.particle1particle2_separation_2d_m = Vec2D(0,0)
        self.particle1particle2_separation_m = 0
        self.particle1particle2_normalized_2d = Vec2D(0,0)

        self.length_in_meters = length_in_meters
        self.strength_Npm = strength_Npm
        self.damper_Ns2pm2 = 0.5 #5.0 #0.05 #0.15
        self.unstretched_width_in_meters = width_in_meters #0.05

        self.spring_vertices_in_meters = []
        self.spring_vertices_in_pixels = []

        self.spring_color = spring_color
        self.draw_as_line = False


    def calc_spring_forces_on_particles(self):
        self.particle1particle2_separation_2d_m = self.particle1.position_in_meters - self.particle2.position_in_meters

        self.particle1particle2_separation_m =  self.particle1particle2_separation_2d_m.length()

        self.particle1particle2_normalized_2d = self.particle1particle2_separation_2d_m / self.particle1particle2_separation_m

        # Spring force:  acts along the separation vector and is proportional to the seperation distance.
        spring_force_on_1_N = self.particle1particle2_normalized_2d * (self.length_in_meters - self.particle1particle2_separation_m) * self.strength_Npm

        # Damper force:  acts along the separation vector and is proportional to the relative speed.
        v_relative_2d_mps = self.particle1.velocity - self.particle2.velocity
        v_relative_alongNormal_2d_mps = v_relative_2d_mps.projection_onto(self.particle1particle2_normalized_2d)
        damper_force_on_1_N = v_relative_alongNormal_2d_mps * self.damper_Ns2pm2

        # Net force by both spring and damper
        SprDamp_force_2d_N = spring_force_on_1_N - damper_force_on_1_N

        # This force acts in opposite directions for each of the two pucks. Notice the "+=" here, this
        # is an aggregate across all the springs. This aggregate MUST be reset (zeroed) after the movements are
        # calculated. So by the time you've looped through all the springs, you get the NET force, one each ball,
        # applied of all individual springs.
        self.particle1.SprDamp_force_2d_N += SprDamp_force_2d_N * (+1)
        self.particle2.SprDamp_force_2d_N += SprDamp_force_2d_N * (-1)

    def width_to_draw_m(self):
        width_in_meters = self.unstretched_width_in_meters * (1 + 0.30 * (self.length_in_meters - self.particle1particle2_separation_m))
        if width_in_meters < (0.05 * self.unstretched_width_in_meters):
            self.draw_as_line = True
            width_in_meters = 0.0
        else:
            self.draw_as_line = False
        return width_in_meters

    def draw(self):
        # Change the width to indicate the stretch or compression in the spring. Note, it's good to
        # do this outside of the main calc loop (using the rendering timer). No need to do all this each
        # time step.

        width_in_meters = self.width_to_draw_m()

        # Calculate the four corners of the spring rectangle.
        particle1particle2_perpendicular_2d = self.particle1particle2_normalized_2d.rotate90()
        self.spring_vertices_in_meters = []
        self.spring_vertices_in_meters.append(self.particle1.position_in_meters + (particle1particle2_perpendicular_2d * width_in_meters))
        self.spring_vertices_in_meters.append(self.particle1.position_in_meters - (particle1particle2_perpendicular_2d * width_in_meters))
        self.spring_vertices_in_meters.append(self.particle2.position_in_meters - (particle1particle2_perpendicular_2d * width_in_meters))
        self.spring_vertices_in_meters.append(self.particle2.position_in_meters + (particle1particle2_perpendicular_2d * width_in_meters))

        # Transform from world to screen.
        self.spring_vertices_in_pixels = []
        for vertice_2d_m in self.spring_vertices_in_meters:
            self.spring_vertices_in_pixels.append( nature.ConvertWorldToScreen( vertice_2d_m))

        # Draw the spring
        if self.draw_as_line == True:
            pygame.draw.aaline(surface_window.surface, self.spring_color, nature.ConvertWorldToScreen(self.particle1.position_in_meters),
                                                                       nature.ConvertWorldToScreen(self.particle2.position_in_meters))
        else:
            pygame.draw.polygon(surface_window.surface, self.spring_color, self.spring_vertices_in_pixels)

def create(user_input):
    surface_window.update_caption("Platform" + str(user_input))

    if user_input == 1:
        space.particles.append( Particle(Vec2D(2.5, 7.5), 0.25, 0.3, THECOLORS["orange"]))
        space.particles.append( Particle(Vec2D(6.0, 2.5), 0.45, 0.3))
        space.particles.append( Particle(Vec2D(7.5, 2.5), 0.65, 0.3))
        space.particles.append( Particle(Vec2D(2.5, 5.5), 1.65, 0.3))
        space.particles.append( Particle(Vec2D(7.5, 7.5), 0.95, 0.3))

    elif user_input == 4:
        spacing_factor = 1.0
        grid_size = 9,6   #9,6
        for j in range(grid_size[0]):
            for k in range(grid_size[1]):
                if ((j,k) == (2,2)):
                    space.particles.append(Particle(Vec2D(spacing_factor*(j+1), spacing_factor*(k+1)), 0.25, 5.0, THECOLORS["orange"]))
                else:
                    space.particles.append(Particle(Vec2D(spacing_factor*(j+1), spacing_factor*(k+1)), 0.25, 5.0))

    elif user_input == 3:
        spacing_factor = 1.5
        grid_size = 5,3
        for j in range(grid_size[0]):
            for k in range(grid_size[1]):
                if ((j,k) == (2,2)):
                    space.particles.append( Particle(Vec2D(spacing_factor*(j+1), spacing_factor*(k+1)), 0.55, 0.3, THECOLORS["orange"]))
                else:
                    space.particles.append( Particle(Vec2D(spacing_factor*(j+1), spacing_factor*(k+1)), 0.55, 0.3))

    elif user_input == 2:
        spacing_factor = 2.0
        grid_size = 4,2
        for j in range(grid_size[0]):
            for k in range(grid_size[1]):
                if ((j,k) == (1,1)):
                    space.particles.append( Particle(Vec2D(spacing_factor*(j+1), spacing_factor*(k+1)), 0.75, 0.3, THECOLORS["orange"]))
                else:
                    space.particles.append( Particle(Vec2D(spacing_factor*(j+1), spacing_factor*(k+1)), 0.75, 0.3))

    elif user_input == 6:
        space.particles.append( Particle(Vec2D(2.00, 3.00),  0.65, 0.3) )
        space.particles.append( Particle(Vec2D(3.50, 4.50),  0.65, 0.3) )
        space.particles.append( Particle(Vec2D(5.00, 3.00),  0.65, 0.3) )

        space.particles.append( Particle(Vec2D(3.50, 7.00),  0.95, 0.3) )

        spring_strength_Npm2 = 200.0
        spring_length_in_meters = 2.5
        spring_width_in_meters = 0.07
        space.springs.append( Spring(space.particles[0], space.particles[1],
                                         spring_length_in_meters, spring_strength_Npm2, width_in_meters=spring_width_in_meters))
        space.springs.append( Spring(space.particles[1], space.particles[2],
                                         spring_length_in_meters, spring_strength_Npm2, width_in_meters=spring_width_in_meters))
        space.springs.append( Spring(space.particles[2], space.particles[0],
                                         spring_length_in_meters, spring_strength_Npm2, width_in_meters=spring_width_in_meters))

    elif user_input == 5:
        space.particles.append( Particle(Vec2D(2.00, 3.00),  0.4, 0.3) )
        space.particles.append( Particle(Vec2D(3.50, 4.50),  0.4, 0.3) )

        spring_strength_Npm2 = 20.0
        spring_length_in_meters = 1.5
        space.springs.append( Spring(space.particles[0], space.particles[1], spring_length_in_meters, spring_strength_Npm2, width_in_meters=0.2))
    else:
        print("Nothing set up for this key.")


def main():
    global nature, surface_window,space
    pygame.init()
    clock = pygame.time.Clock()

    window = (800, 700)
    nature = Environment(window, 10.0)
    surface_window = GameWindow(window, 'Platform')
    space = Space({"L_m":0.0, "R_m":surface_window.UpperRight.x, "B_m":0.0, "T_m":surface_window.UpperRight.y})
    space.correct_for_wall_penetration = True
    space.correct_for_particle_penetration = True

    create(3)

    FPS = 500
    dt_render_s = 0.0
    dt_render_limit_s = 1.0/120.0

    while True:
        dt_physics_s = float(clock.tick(FPS) * 1e-3)
        if (dt_physics_s < 0.10):
            user_input = nature.get_local_user_input()
            if user_input in [0,1,2,3,4,5,6,7,8,9]:
                print(user_input)
                space.particles = []
                space.controlled_particles = []
                space.springs = []

                surface_window.clear()
                create(user_input)

            for client_name in nature.clients:
                nature.clients[client_name].calc_string_forces_on_particles()

            for spring in space.springs:
                spring.calc_spring_forces_on_particles()

            for eachparticle in space.particles:
                space.update_particleSpeedAndPosition(eachparticle, dt_physics_s)

            space.check_for_collisions()
            if (dt_render_s > dt_render_limit_s):
                if space.correct_for_particle_penetration:
                    surface_window.surface.fill((0,0,0))
                else:
                    grey_level = 40
                    surface_window.surface.fill((grey_level,grey_level,grey_level))
                space.draw()
                for particle in space.particles:
                    particle.draw()

                for spring in space.springs:
                    spring.draw()

                for client_name in nature.clients:
                    if (nature.clients[client_name].selected_particle != None):
                        nature.clients[client_name].draw_cursor_string()
                pygame.display.flip()
                dt_render_s = 0

            dt_render_s += dt_physics_s

main()
