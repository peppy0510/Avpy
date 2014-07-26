#!/usr/bin/env python

'''
Decode the 5th first frame of the first video stream and write bmp (require PySDL2)

python outputBMP.py -m file.avi -> save frame 1 to 5
python outputBMP.py -m file.avi -o 140 -> save frame 140 to 145
'''

import sys
import ctypes
import copy

import sdl2

from pyav import Media

if __name__ == '__main__':

    # cmdline
    from optparse import OptionParser

    usage = "usage: %prog -m foo.avi -o 140"
    parser = OptionParser(usage=usage)
    parser.add_option('-m', '--media', 
            help='play media')
    parser.add_option('-o', '--offset', 
            type='int',
            help='frame offset', default=0)
    parser.add_option('-c', '--frameCount', 
            type='int',
            help='number of image to save (default: %default)', default=5)
    parser.add_option('--copyPacket', 
            action='store_true',
            help='copy packet (debug only)')

    (options, args) = parser.parse_args()

    if not options.media:
        print('Please provide a media to play with -m or --media option')
        sys.exit(1)
    
    try:
        m = Media(options.media)
    except IOError as e:
        print('Unable to open %s: %s' % (options.media, e))
        sys.exit(1)

    # dump info
    mediaInfo = m.info()

    # select first video stream
    vstreams = [ i for i, s in enumerate(mediaInfo['stream']) if s['type'] == 'video' ]
    if vstreams:
        vstream = vstreams[0]
    else:
        print('No video stream in %s' % mediaInfo['name'])
        sys.exit(2)

    streamInfo = mediaInfo['stream'][vstream]
    size = streamInfo['width'], streamInfo['height']

    print('video stream index: %d' % vstream)
    print('video stream resolution: %dx%d' % (size[0], size[1]))

    #m.addScaler(vstream)
    m.addScaler2(vstream, *size)

    # sdl2
    sdl2Version = sdl2.version_info
    print('Using sdl2 version: %d.%d.%d' % 
            (sdl2Version[0], sdl2Version[1], sdl2Version[2]))
    if sdl2.SDL_Init(0) != 0:
        print(sdl2.SDL_GetError())
        sys.exit(3)
    
    if sdl2.SDL_BYTEORDER == sdl2.SDL_LIL_ENDIAN:
        rmask = 0x000000ff
        gmask = 0x0000ff00
        bmask = 0x00ff0000
        amask = 0xff000000
    else:
        rmask = 0xff000000
        gmask = 0x00ff0000
        bmask = 0x0000ff00
        amask = 0x000000ff

    decodedCount = 0
    for p in m:
        
        if p.streamIndex() == vstream:
           
            if options.copyPacket:
                p2 = copy.copy(p) 
            else:
                p2 = p

            p2.decode()
            if p2.decoded:

                decodedCount += 1
                print('decoded frame %d' % decodedCount)

                if decodedCount >= options.offset:
                    print('saving frame...')
                    
                    buf = p2.swsFrame.contents.data[0]
                    
                    surface = sdl2.SDL_CreateRGBSurfaceFrom(buf, 
                            size[0], size[1], 24, 
                            size[0] * 3,
                            rmask, gmask,
                            bmask, amask)
                    sdl2.SDL_SaveBMP(surface, 'frame.%d.bmp' % decodedCount)
                    sdl2.SDL_FreeSurface(surface)

                if decodedCount >= options.offset + options.frameCount:
                    break 