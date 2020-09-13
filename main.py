import argparse
import qrcode
from PIL import Image, ImageEnhance, ImageFilter, ImageFont, ImageDraw

from opsys import operating_systems


class Stats:
    stats_file = 'log.txt'
    message = ''

    def save(self):
        with open(file=self.stats_file, mode='w') as f:
            f.write(self.message)

    def add(self, data):
        self.message += '{}\n'.format(data)


stats = Stats()


class Output:
    class Dimensions:
        width = 600
        height = 200

    padding = 1
    bigvspace = 5
    vspace = 0
    dimensions = Dimensions()

    out_file = 'sticker.png'

    qrcode = None

    serial = None
    serial_size = 24
    serial_chunK = 30

    name = None
    name_size = 48
    name_chunk = 13

    os_logo = None


output = Output()


class QrContents:
    qr_type = 0
    qr_correction = 'M'
    qr_string = None

    class Wifi:
        ssid = None
        password = None
        encryption = 'nopass'
        hidden = None

    wifi = Wifi()

    def make_wifi_string(self):
        self.qr_string = 'WIFI:T:{};S:{};P:{};H:{};'.format(
            self.wifi.encryption, self.wifi.ssid, self.wifi.password, self.wifi.hidden)


contents = QrContents()


def analize_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('-o', '--output', type=str,
                        help='path to output image')

    parser.add_argument('-n', '--name', type=str,
                        help='name displayed on sticker, can be splitted with /')
    parser.add_argument('-s', '--serial', type=str,
                        help='serial displayed on sticker')
    parser.add_argument('-c', '--operating-system',
                        help='logo of operating system displayed on the background')

    parser.add_argument('-Q', '--qrcode-correction',
                        type=str, help='qrcode error correction level',
                        choices=['L', 'M', 'Q', 'H'])
    parser.add_argument('-T', '--type', type=int,
                        help='QR Code type. Possible values: 0 - string, 1 - wifi',
                        choices=[0, 1])

    parser.add_argument('-S', '--string', type=str,
                        help='string encoded inside QR code')
    parser.add_argument('-F', '--file', type=str,
                        help='file containing string encoded inside QR code')

    parser.add_argument('-E', '--encryption', type=str,
                        help='encryption of the WiFi encoded inside QR code, if not specified assuming nopass',
                        choices=['nopass', 'WEP', 'WPA'])
    parser.add_argument('-I', '--ssid', type=str,
                        help='ssid of the WiFi encoded inside QR code')
    parser.add_argument('-P', '--password', type=str,
                        help='password of the WiFi encoded inside QR code')
    parser.add_argument('-H', '--hidden', type=str,
                        help='true if the WiFi is hidden',
                        choices=['true'])

    args = parser.parse_args()

    stats.add(args)

    if args.type:
        contents.qr_type = args.type

    if args.output:
        output.out_file = args.output

    if args.name:
        output.name = args.name.split('/')
        tmp = []
        for chunk in output.name:
            tmp += [chunk[i:i+output.name_chunk]
                    for i in range(0, len(chunk), output.name_chunk)]
        output.name = tmp

        if len(output.name) > 2:
            print('Name is too long!')
            exit(1)

    if args.serial:
        if len(args.serial) >= 30:
            output.serial = [args.serial[i:i+output.serial_chunK]
                             for i in range(0, len(args.serial), output.serial_chunK)]
        else:
            output.serial = [args.serial]

        if len(output.serial) > 3:
            print('Serial is too long!')
            exit(1)

    if args.operating_system:
        if args.operating_system in operating_systems:
            output.os_logo = args.operating_system
        else:
            for os in operating_systems:
                if args.operating_system in os:
                    print('Assuming {} as {}'.format(
                        args.operating_system, os))
                    output.os_logo = os
                    break
            if output.os_logo == None:
                print('Did not found matching operating system!')
                exit(1)

    if args.qrcode_correction:
        contents.qr_correction = args.qrcode_correction

    if args.string:
        if contents.qr_type != 0:
            print('You are trying to create string and WiFi QR Code at the same time!')
            exit(1)
        elif contents.qr_type == 0:
            contents.qr_string = args.string

    if args.file:
        if contents.qr_type != 0:
            print('You are trying to create string and WiFi QR Code at the same time!')
            exit(1)
        elif args.string:
            print('Unable to embedd two strings inside QR Code!')
            exit(1)
        elif contents.qr_type == 0:
            with open(args.file) as f:
                line = f.readline()
                contents.qr_string = line
                while True:
                    line = f.readline()
                    if line:
                        contents.qr_string += line
                    else:
                        break

    if args.encryption:
        contents.wifi.encryption = args.encryption

    if args.ssid:
        if contents.qr_type != 1:
            print(
                'You are tring to create WiFi QR Code with wrongly specified QR Code type!')
            exit(1)
        else:
            if args.password:
                if contents.wifi.encryption != 'nopass':
                    contents.wifi.ssid = args.ssid
                    contents.wifi.password = args.password

                    if args.hidden:
                        contents.wifi.hidden = args.hidden
                else:
                    print(
                        'You did not specified correct encryption method and provided password!')
                    exit(1)
            else:
                if contents.wifi.encryption != 'nopass':
                    print('You did not provided password!')
                    exit(1)

        contents.make_wifi_string()


def qrify():
    if contents.qr_correction == 'L':
        correction = qrcode.constants.ERROR_CORRECT_L
    elif contents.qr_correction == 'M':
        correction = qrcode.constants.ERROR_CORRECT_M
    elif contents.qr_correction == 'Q':
        correction = qrcode.constants.ERROR_CORRECT_Q
    elif contents.qr_correction == 'H':
        correction = qrcode.constants.ERROR_CORRECT_H

    qr = qrcode.QRCode(
        version=2,
        error_correction=correction,
        box_size=5,
        border=5
    )

    qr.add_data(contents.qr_string)
    qr.make(fit=True)

    img = qr.make_image(fill_color='black', back_color='white')

    stats.add(img.size)

    return img


def stickerize(qr):
    (w, h) = qr.size

    output.dimensions.height = h
    output.dimensions.width = w*3
    output.padding = int(output.dimensions.height * 0.01)
    print(output.padding)
    if output.padding == 0:
        output.padding = 1

    output.name_size = int(h / 4)
    output.serial_size = int(h / 8)

    sticker = Image.new(
        mode='RGB',
        size=(output.dimensions.width, output.dimensions.height),
        color=(255, 255, 255)
    )

    qr = qr.resize((output.dimensions.height, output.dimensions.height))

    sticker.paste(qr, (1, 1))

    if output.os_logo:
        fname = 'resources/images/{}.png'.format(output.os_logo)
        os = Image.open(fname).convert('RGBA')
        os.thumbnail((output.dimensions.height, output.dimensions.width))

        (w, h) = os.size
        bg_os = Image.new(
            mode='RGB',
            size=(w, h),
            color=(255, 255, 255)
        )

        bg_os.paste(os, (0, 0), os)
        bg_os.putalpha(64)
        bg_os.filter(ImageFilter.SMOOTH_MORE)

        (w1, h1) = sticker.size

        sticker.paste(bg_os,
                      (w1 - w - 1, int((h1 - 2*output.padding - h)/2)),
                      bg_os)

    draw = ImageDraw.Draw(sticker)
    font_regular = ImageFont.truetype(
        'resources/fonts/Ubuntu-Regular.ttf', output.name_size)
    font_monospace = ImageFont.truetype(
        'resources/fonts/UbuntuMono-Regular.ttf', output.serial_size)

    pos = int(output.dimensions.height/2) - \
        int(output.name_size) * len(output.name) + output.bigvspace
    for chunk in output.name:
        draw.text(
            xy=(output.dimensions.height + output.padding, pos),
            text=chunk,
            fill=(0, 0, 0),
            font=font_regular,
            align='center'
        )

        pos = pos + int(output.name_size) - 3

    if output.serial:
        pos = int(output.dimensions.height/2) + output.bigvspace
        for chunk in output.serial:
            draw.text(
                xy=(output.dimensions.height + output.padding, pos),
                text=chunk,
                fill=(0, 0, 0),
                font=font_monospace,
                align='center'
            )

            pos = pos + int(output.serial_size) + output.vspace

    bg = Image.new(
        mode='RGB',
        size=(output.dimensions.width + 2*output.padding,
              output.dimensions.height + 2*output.padding),
        color=(0, 0, 0)
    )

    bg.paste(sticker, (output.padding, output.padding))

    return bg


def main():
    analize_args()

    qrimg = qrify()
    sticker = stickerize(qrimg)

    sticker.save(output.out_file)


if __name__ == '__main__':
    main()

    stats.save()
