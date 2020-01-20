# * 
# * Copyright (c) 2020, ecuunlock
# *
# * EMAIL = engineering@ecuunlock.com
# * WEBSITE = www.ecuunlock.com
# * PHONE = (419)-330-9774
# *
# * All rights reserved.
# * Redistribution and use in source and binary forms, with or without modification, 
# * are permitted provided that the following conditions are met:
# * Redistributions of source code must retain the above copyright notice, this list 
# * of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice, this 
# * list of conditions and the following disclaimer in the documentation and/or other
# * materials provided with the distribution.
# * Neither the name of the organization nor the names of its contributors may be 
# * used to endorse or promote products derived from this software without specific 
# * prior written permission.
# * 
# * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# * CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# * EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# * PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# * PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# * LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# * NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# *

class UnlockAlgorithm:

    def __init__(self):
    
        return

    def finder(self, data, sup, var, unlockLevel):
    
        dataIn = int(str(data).replace(' ', '')[12:], 16)
        
        # print(dataIn)
        
        # print(var)
        
        # print(sup)
        
        if sup == '36' and unlockLevel == 1:
        
            Key = self.L1_36_22(dataIn)
            
            getKey = [Key[0], Key[1], Key[2], Key[3]]
            
            return getKey

    @staticmethod
    def L1_36_22(seed):
    
        # print(seed)
        
        KEY_CONSTANT_1 = 0x11111111       # HAHA YOU DIDNT REALLY THINK I WAS GONNA GIVE YOU AN ALGO FOR FREE DID YOU!!

        KEY_CONSTANT_2 = 0x11111111

        AND_CONSTANT = 4294967295

        tempSeed = ((seed >> 16) & 0xFF) << 24

        tempSeed += ((seed >> 24) & 0xFF) << 16

        tempSeed += (seed >> 8) & 0xFF

        tempSeed += (seed & 0xFF) << 8

        shift_seed = ((tempSeed << 11) + (tempSeed >> 22)) & AND_CONSTANT

        key = (shift_seed ^ (KEY_CONSTANT_1 ^ (KEY_CONSTANT_2 & seed))) & AND_CONSTANT

        key = ("0x%X" % key).replace("0x", "", 1)
        
        # print(key)

        seed_a, seed_b, seed_c, seed_d = (
            int(key[0:2], 16),
            int(key[2:4], 16),
            int(key[4:6], 16),
            int(key[6:8], 16),
        )

        # print(seed_a, seed_b, seed_c, seed_d)

        return seed_a, seed_b, seed_c, seed_d
