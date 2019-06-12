import math

class Vec2D:
    '''
        Компоненты вектора могут быть введены, как отдельные аргументы или как
        пара кортежей в одном аргументе
    '''
    def __init__(self, x_or_pair, y = None, int_flag = "not_int"):
        if y == None:
            self.x = x_or_pair[0]
            self.y = x_or_pair[1]
        else:
            self.x = x_or_pair
            self.y = y

        if int_flag == "int":
            self.x = int(round(self.x))
            self.y = int(round(self.y))
        else:
            self.x = float(self.x)
            self.y = float(self.y)

    # Две функции, которые устанавливают формат выходной строки. Вывод вектора(экземпляра объекта)
    def __repr__(self):
        return 'Vec2D({}, {})'.format(self.x, self.y)
    def __str__(self):
        return '({}, {})'.format(self.x, self.y)

    '''
        =======================================================================
        В этом разделе определяются методы векторной арифметики и сравнения.
        Перегрузка операторов устанавливаются здесь же.
        =======================================================================
    '''

    # Сумма векторов
    def add_vector(self, vec_B):
        return Vec2D(self.x + vec_B.x, self.y + vec_B.y)
    def __add__(self, vec_B):
        return Vec2D(self.x + vec_B.x, self.y + vec_B.y)

    # Разность векторов
    def sub_vector(self, vec_B):
        return Vec2D(self.x - vec_B.x, self.y - vec_B.y)
    def __sub__(self, vec_B):
        return Vec2D(self.x - vec_B.x, self.y - vec_B.y)

    '''
     Операции масштабирования. Следует учесть, что случай перегрузки оператора
     должен иметь вектор, предшествующий коэффициенту масштабирования.
     Например, vector * 2.1 или vector / 4.0, но не 2.1 * vector.
    '''
    def scale_vector(self, scale_factor):
        return Vec2D( self.x * scale_factor, self.y * scale_factor)
    def __mul__(self, scale_factor):
        return Vec2D( self.x * scale_factor, self.y * scale_factor)
    def __truediv__(self, scale_factor):
        return Vec2D( self.x / scale_factor, self.y / scale_factor)

    # Сравнения.
    def equal(self, vec_B):
        return (self.x == vec_B.x) and (self.y == vec_B.y)
    def not_equal(self, vec_B):
        return (self.x != vec_B.x) or (self.y != vec_B.y)

    '''
     =========================================================================
     Определние длины вектора. Используется операция квадратного корня
    '''
    def length(self):
        return (self.x*self.x + self.y*self.y)**0.5

    # Длина в квадрате иногда может быть использована вместо масштабной длины
    # вектора. Длина в квадрате вычисляется намного быстрее, так как нет отперации
    # с квадратным корнем
    def length_squared(self):
        return (self.x*self.x + self.y*self.y)

    # Возвращает вектор в том же направлении, что и оригинал, но с длиной 1
    # (единичная длина)
    def normal(self):
        return self / self.length()

    # Возвращает вектор в том же направлении, что и оригинал, но с длиной,
    # равной выбранной величине
    def set_magnitude(self, magnitude_target):
        return self.normal() * target_magnitude

    # Скалярное произведение с дргуим вектором.
    def dot(self, vec_B):
        return (self.x * vec_B.x) + (self.y * vec_B.y)

    # Векторная составляющая собственного вектора вдоль направления вектора B.
    def projection_onto(self, vec_B):
        vB_dot_vB = vec_B.dot(vec_B)
        if (vB_dot_vB > 0):
            return vec_B * ( self.dot(vec_B) / vB_dot_vB )
        else:
            # Если vec_B имеет нулевую величину, вернуть вектор нулевой величины.
            # В этом случае скалярное произведение двух векторов будет равно нулю.
            # Это оставляет проекцию неопределенной; vec_B*(0/0). Было бы целесообразно
            # вернуть значение None здесь. Но вектор нулевой величины удобен для работы
            # с шайбами, закрепленными пружиной(поскольку расстояние между шайбами и точкой
            # закрепления в конечном итоге сводится к нулю, поскольку нарушенная шайба теряет
            # энергию).
            return self * 0

    # Повернуть против часовой стрелки на 90 градусов
    def rotate90(self):
        return Vec2D(-self.y, self.x)

    # Переворот(обратное направление вектора).
    def rotate180(self):
        return Vec2D(-self.x, -self.y)

    # Повернуть (изменить направление) исходного вектора на указаноое количество градусов.
    # (Исходный вектор повернут нга angle_degrees)
    def rotated(self, angle_degrees, sameVector=False):
        angle_radians = math.radians(angle_degrees)
        cos = math.cos(angle_radians)
        sin = math.sin(angle_radians)
        # Преобразование вращения.
        x = self.x * cos - self.y * sin
        y = self.x * sin + self.y * cos
        if sameVector:
            # Изменить исходный вектор.
            self.x = x
            self.y = y
        else:
            # Новый векторный объект
            return Vec2D(x, y)

    # Установите направление вектора на определенный угол.
    def set_angle(self, angle_degrees):
        self.x = self.length()
        self.y = 0
        return self.rotated(angle_degrees)

    # Определите угол, который этот вектор делает с остью x. Измерьте против часовой
    # стрелки от оси x.
    def get_angle(self):
        if (self.length_squared() == 0):
            return 0
        return math.degrees(math.atan2(self.y, self.x))

    # Определить угол между двумя векторами.
    def get_angle_between(self, vec_B):
        cross = self.x*vec_B.y - self.y*vec_B.x    #= ABsin(theta)
        dot   = self.x*vec_B.x + self.y*vec_B.y    #= ABcos(theta)
        # Используется форма ввода двух параметров (x,y) арктангенса. Это безопаснее, чем взять арктангенс произведения
        # перекрестного/скалярного, который может быть нулевым в знаменателе.
        return math.degrees(math.atan2(cross, dot))

    # Возвращает кортеж, содержащий две составляющие вектора
    def tuple(self):
        return (self.x, self.y)
