from PIL import Image

class CustomScript:
    def __init__(self):
        print('Sukurtas CustomScript objektas is desktop folderio')

    def ShowPicture(self):
        image = Image.open('/home/ubuntu/Desktop/CustomScriptFolder/attack_script/attack.jpg')
        image.show()


script = CustomScript()
script.ShowPicture()
