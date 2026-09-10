#!/usr/bin/env python3
"""Bounded-by-caller native AAL open/size probe. No preview, photo or video.

Usage: timeout -k 2 20 runuser -u droidian -- python3 eqs-camera-probe.py CAMERA_ID
ABI: libhybris 99bb609 camera compatibility headers. Never run in recovery/chroot.
"""
import ctypes as C
import os
import sys


def main():
    camera_id = int(sys.argv[1])
    if os.geteuid() == 0 or camera_id not in range(8):
        raise SystemExit('Refusing root or out-of-range camera ID')
    if not os.path.exists('/run/systemd/system') or not os.path.exists('/dev/binder'):
        raise SystemExit('Native Droidian with binder required; not recovery')
    # Exact nine-pointer CameraControlListener ABI. No callbacks request images.
    class Listener(C.Structure):
        _fields_ = [(name, C.c_void_p) for name in ('error', 'shutter', 'focus', 'zoom',
                      'raw', 'compressed', 'texture', 'context', 'preview')]
    assert C.sizeof(Listener) == 9 * C.sizeof(C.c_void_p)
    lib = C.CDLL('libcamera.so.1')
    def function(name, result, *args):
        fn = getattr(lib, 'android_camera_' + name)
        fn.restype, fn.argtypes = result, args
        return fn
    count = function('get_number_of_devices', C.c_int)
    info = function('get_device_info', C.c_int, C.c_int32, C.POINTER(C.c_int), C.POINTER(C.c_int))
    connect = function('connect_by_id', C.c_void_p, C.c_int32, C.POINTER(Listener))
    disconnect = function('disconnect', None, C.c_void_p)
    cb_type = C.CFUNCTYPE(None, C.c_void_p, C.c_int, C.c_int)
    error_type = C.CFUNCTYPE(None, C.c_void_p)
    @error_type
    def error(_):
        print('CAMERA_ASYNC_ERROR', flush=True)
    listener = Listener()
    listener.error = C.cast(error, C.c_void_p)
    total = count()
    print(f'CAMERA_COUNT={total} UID={os.geteuid()} ID={camera_id}', flush=True)
    if total < 0 or total > 8 or camera_id >= total:
        raise SystemExit('Requested ID not exposed')
    facing, orientation = C.c_int(-1), C.c_int(-1)
    rc = info(camera_id, C.byref(facing), C.byref(orientation))
    print(f'CAMERA_INFO result={rc} facing={facing.value} orientation={orientation.value}', flush=True)
    print('CAMERA_OPEN_BEGIN', flush=True)
    camera = connect(camera_id, C.byref(listener))
    if not camera:
        raise SystemExit('CAMERA_OPEN_FAILED')
    print('CAMERA_OPEN_OK', flush=True)
    try:
        for kind in ('picture', 'preview', 'video'):
            sizes = set()
            @cb_type
            def size(_, width, height):
                if 0 < width <= 32768 and 0 < height <= 32768 and len(sizes) < 512:
                    sizes.add((width, height))
            enum = function('enumerate_supported_' + kind + '_sizes', None, C.c_void_p, cb_type, C.c_void_p)
            enum(camera, size, None)
            ordered = sorted(sizes, key=lambda x: x[0]*x[1], reverse=True)
            print(f'CAMERA_{kind.upper()}_SIZES={ordered}', flush=True)
            if not ordered:
                print(f'CAMERA_NO_{kind.upper()}_SIZES', flush=True)
    finally:
        disconnect(camera)
        print('CAMERA_DISCONNECTED', flush=True)


if __name__ == '__main__':
    main()
