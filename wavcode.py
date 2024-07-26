import os, sys, getopt, wave
spread_default = 8 #place data every n samples
message_max = 524288 #max file size for encode_raw
#the default message_max is 512 KiB, which at spread=8 theoretically requires a 32 MiB .wav input to fit

def usage():
    print("usage: wavcode.py [audio file] [output file] [-e message] [-s #]")
    print("   OR: wavcode.py [audio file] [output file] -r [-e message file] [-s #]")
    print("option -e: encode a message")
    print("option -r: operate in binary mode (use a file instead)")
    print("option -s: custom spread value (place/read data every #th sample)")

def encode(infile, outfile="result.wav", message="ENCODED TEST MESSAGE", spread=spread_default):
    with wave.open(infile, 'rb') as input:
        #check sizes
        inputsize = input.getnframes()
        messagesize = len(message)
        if messagesize >= (inputsize / spread):
            print("Message too large to fit in audio! Try a larger audio file, or lower the spread value with the -s option.")
            exit()

        #read data
        framebytes = bytearray(input.readframes(input.getnframes()))
        messagebytes = bytearray(str.encode(message))

        #manipulate audio frames
        frameindex = 0
        for byte in messagebytes:
            for b in range(8):
                messagebit = byte & (1<<b)
                framebytes[frameindex*spread] = (framebytes[frameindex*spread] & (255<<1)) | messagebit
                frameindex += 1

        #write to output
        with wave.open(outfile, 'wb') as output:
            output.setparams(input.getparams())
            output.writeframes(framebytes)
        
        print("Encoding finished. Saved result to", outfile)

def encode_raw(infile, outfile="result.wav", message="wavcode.py", spread=spread_default):
    with wave.open(infile, 'rb') as input:
        with open(message, 'rb') as messagefile:
            #check sizes
            inputsize = input.getnframes()
            messagefile.seek(0, os.SEEK_END)
            messagesize = messagefile.tell()
            messagefile.seek(0)
            if messagesize >= (inputsize / spread):
                print("Message too large to fit in audio! Try a larger audio file, or lower the spread value with the -s option.")
                exit()
            elif messagesize >= message_max:
                print("Message too large to process! Compress/truncate the message file, or modify the maximum filesize in the script if necessary.")
                exit()

            #read data
            framebytes = bytearray(input.readframes(input.getnframes()))
            messagebytes = bytearray()
            while True:
                buffer = messagefile.read(1)
                if not buffer:
                    break
                messagebytes.append(buffer[0])

            #manipulate audio frames
            frameindex = 0
            for byte in messagebytes:
                for b in range(8):
                    messagebit = byte & (1<<b)
                    framebytes[frameindex*spread] = (framebytes[frameindex*spread] & (255<<1)) | messagebit
                    frameindex += 1

            #write to output
            with wave.open(outfile, 'wb') as output:
                output.setparams(input.getparams())
                output.writeframes(framebytes)
            
            print("Raw encoding finished. Saved result to", outfile)

def decode(infile, outfile="result.txt", spread=spread_default):
    with wave.open(infile, 'rb') as input:
        #read data
        framebytes = bytearray(input.readframes(input.getnframes()))

        #read from audio frames
        messagebytes = ""
        frameindex = 0
        while frameindex*spread < len(framebytes):
            bits = []
            for b in range(8):
                messagebit = framebytes[frameindex*spread] & 1
                bits.insert(0, messagebit)
                frameindex += 1
            #convert bits array to a value
            newbyte = sum(v << i for i, v in enumerate(bits[::-1]))
            messagebytes += (chr(newbyte))

        #write to output
        with open(outfile, 'wt') as output:
            output.write(messagebytes)
        print("Decoding finished. Read", frameindex, "frames. Saved result to", outfile)

def decode_raw(infile, outfile="result.bin", spread=spread_default):
    with wave.open(infile, 'rb') as input:
        #read data
        framebytes = bytearray(input.readframes(input.getnframes()))

        #read from audio frames
        messagebytes = bytearray()
        frameindex = 0
        
        while frameindex < len(framebytes)-(spread*8):
            bits = []
            for b in range(8):
                messagebit = framebytes[frameindex] & 1
                bits.insert(0, messagebit)
                frameindex += spread
                print(frameindex, "/", len(framebytes), ":", messagebit)
            #convert bits array to a value
            newbyte = sum(v << i for i, v in enumerate(bits[::-1]))
            messagebytes.append(newbyte)

        #write to output
        with open(outfile, 'wb') as output:
            output.write(messagebytes)
        print("Decoding finished. Read", frameindex, "frames. Saved result to", outfile)

if len(sys.argv) < 3:
    usage()
else:
    rawmode = False
    encodemode = False
    arg_infile = sys.argv[1]
    arg_outfile = sys.argv[2]
    arg_message = None
    arg_spread = spread_default
    try:
        args, vals = getopt.getopt(sys.argv[3:], "e:rs:", ["encode", "raw", "spread"])

        for i, v in args:
            if i in ("-e", "--encode"):
                encodemode = True
                arg_message = v
            if i in ("-r", "--raw"):
                rawmode = True
            if i in ("-s", "--spread"):
                arg_spread = v

        #clumsy but works
        if rawmode and encodemode:
            encode_raw(arg_infile, arg_outfile, arg_message, arg_spread)
        elif rawmode:
            decode_raw(arg_infile, arg_outfile, arg_spread)
        elif encodemode:
            encode(arg_infile, arg_outfile, arg_message, arg_spread)
        else:
            decode(arg_infile, arg_outfile, arg_spread)

    except getopt.GetoptError as error:
        print (str(error))
        usage()