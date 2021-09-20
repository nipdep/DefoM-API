import cv2

def expect(input, expectedType, field):
    if isinstance(input, expectedType):
        return input
    raise AssertionError("Invalid input for type", field)

def get_RGB(image):
    rgb = cv2.normalize(image[:,:,[2,1,0]], None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    return rgb