from math import log
from enum import Enum
from typing import Iterable


DIMENSION_N_BIT = 4
TYPE_N_BIT = 4
VALUE_N_BIT =  16


class Dimension(int, Enum):
    NOTHING = 0
    OneD = 1
    TwoD = 2
    ThreeD = 3


class Type(int, Enum):
    NOTHING = 0
    Text = 1
    Audio = 2
    Video = 3
    Image = 4


class InfoCell(object):
    """任何一个不可再分信息的表示方式.

    任何一个不可再分信息可以使用以下方式进行无损的表述：
    1. 信息所在的维度；
    2. 信息的类型
    3. 信息的内容
    """

    def __init__(self, dimension: int = 0, type: int = 0, value: int = 0):
        assert dimension < 2 ** DIMENSION_N_BIT
        assert type < 2 ** TYPE_N_BIT
        assert value < 2 ** VALUE_N_BIT

        self.dimension = dimension
        self.type = type
        self.value = value

    def encode(self) -> int:
        """使用 24 个比特对信息进行编码
        高 4 位表示维度
        低 16 位表示值
        剩下 4 位表示类型
        """
        info = 0x0 << DIMENSION_N_BIT
        info = info | self.dimension
        info = info << TYPE_N_BIT
        info = info | self.type
        info = info << VALUE_N_BIT
        info = info | self.value
        return info

    @classmethod
    def decode(cls, encoding: int):
        value = encoding & 0xFFFF
        encoding = encoding >> VALUE_N_BIT
        type = encoding & 0xF
        encoding = encoding >> TYPE_N_BIT
        dimension = encoding & 0xF
        encoding = encoding >> DIMENSION_N_BIT
        assert encoding == 0
        return InfoCell(dimension, type, value)

    # def encode(self) -> float:
    #     """使用 (type + value / 2 ** VALUE_N_BIT) * (2 ** TYPE_N_BIT)**(1 + dimension / 2 ** DIMENSION_N_BIT) 进行编码
    #     """

    #     return (self.type + self.value / 2 ** VALUE_N_BIT) * (2**TYPE_N_BIT) ** (1 + self.dimension / 2 ** DIMENSION_N_BIT)

    # @classmethod
    # def decode(self, encoding: float):
    #     exponent = log(encoding, 2 ** TYPE_N_BIT)
    #     dimension = int((exponent - 1) * 2 ** DIMENSION_N_BIT)

    #     type_plus_value = encoding / (2**TYPE_N_BIT) ** (1 + dimension / 2 ** DIMENSION_N_BIT)
    #     type = int(type_plus_value)
    #     value = int((type_plus_value - type) * 2 ** VALUE_N_BIT)
    #     return InfoCell(dimension, type, value)


    def __repr__(self) -> str:
        return str(self.encode())

    def __str__(self):
        return f"{Type(self.type).name} - {Dimension(self.dimension)}D: {self.value}"


BEGIN_CELL_MAP = {
    Dimension.OneD: InfoCell(Dimension.OneD, 0, 0),
    Dimension.TwoD: InfoCell(Dimension.TwoD, 0, 0),
    Dimension.ThreeD: InfoCell(Dimension.ThreeD, 0, 0),
}

END_CELL_MAP = {
    Dimension.OneD: InfoCell(Dimension.OneD, 0, 1),
    Dimension.TwoD: InfoCell(Dimension.TwoD, 0, 1),
    Dimension.ThreeD: InfoCell(Dimension.ThreeD, 0, 1),
}


def _ravel(somethings, deep: int = 0):
    if deep == 0:
        return somethings
    result = []

    result.append(BEGIN_CELL_MAP[deep])
    for something in somethings:
        if isinstance(something, Iterable):
            sub_result = _ravel(something, deep=deep-1)
            if isinstance(sub_result, list):
                result.extend(sub_result)
            else:
                result.append(sub_result)
        else:
            result.append(something)
    result.append(END_CELL_MAP[deep])

    return result

def encode(cls, something):
    info = []

    somethings = _ravel(something, deep = cls._DIMENSION)
    for something in somethings:
        if something in END_CELL_MAP.values():
            info.append(something.encode())
            continue

        if something in BEGIN_CELL_MAP.values():
            info.append(something.encode())
            continue

        if something not in cls._APPEARD:
            cls._APPEARD.setdefault(
                something, len(cls._APPEARD)
            )
            cls._APPEARD_INV.setdefault(
                len(cls._APPEARD_INV), something,
            )

        cell = InfoCell(
            dimension=cls._DIMENSION,
            type=cls._TYPE,
            value=cls._APPEARD.get(something)
        )

        info.append(cell.encode())

    return info


def decode(cls, somethings):
    if not somethings:
        return []

    elements = []
    while somethings:
        something = somethings.pop(0)

        if something in [v.encode() for v in BEGIN_CELL_MAP.values()]:
            elements.append([])
            continue

        if something in [v.encode() for v in END_CELL_MAP.values()]:
            top = elements.pop()
            if elements:
                elements[-1].append(top)
            else:
                elements = [top]
            continue

        decoded = InfoCell.decode(something)
        elements[-1].append(cls._APPEARD_INV[decoded.value])

    return elements[0]



class MetaEncoder(type):

    def __new__(cls, name, bases, attrs):
        cls = super().__new__(cls, name, bases, attrs)

        if not hasattr(cls, "_TYPE"):
            raise NotImplementedError

        if not hasattr(cls, "_DIMENSION"):
            raise NotImplementedError

        if not hasattr(cls, "_APPEARED"):
            cls._APPEARD = dict()

        if not hasattr(cls, "_APPEARED_INV"):
            cls._APPEARD_INV = dict()


        cls.encode = classmethod(encode)
        cls.decode = classmethod(decode)

        return cls


class Encoder(metaclass=MetaEncoder):

    _TYPE = None

    _DIMENSION = 0


class TextEncoer(Encoder):

    _TYPE = Type.Text

    _DIMENSION = Dimension.OneD


class AudioEncoder(Encoder):

    _TYPE = Type.Audio

    _DIMENSION = Dimension.OneD


class ImageEncoder(Encoder):

    _TYPE = Type.Image

    _DIMENSION = Dimension.TwoD


class VideoEncoder(Encoder):

    _TYPE = Type.Video

    _DIMENSION = Dimension.ThreeD


if __name__ == '__main__':
    text = "hello, world"
    e = TextEncoer.encode(text)
    # print(e)
    print(TextEncoer.decode(e))

    audio = ["it", "is", "a", "speech", "speech"]
    e = AudioEncoder.encode(audio)
    print(e)
    print(AudioEncoder.decode(e))

    image = [[0, 2, 3, 255], [1, 3, 4, 6], [2, 22, 78, 78], [23, 89, 34, 18]]
    e = ImageEncoder.encode(image)
    # print(e)
    print(ImageEncoder.decode(e))

    video = [
        [
            [1, 2],
            [8, 8, 1],
        ],
        [
            [1, 2],
            [8, 8, 9],
        ]
    ]
    e = VideoEncoder.encode(video)
    # print(e)
    print(VideoEncoder.decode(e))

