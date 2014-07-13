/*
 *  cfiler_native.cp
 *  cfiler_native
 *
 *  Created by Shimomura Tomonori on 2014/07/13.
 *  Copyright (c) 2014年 craftware. All rights reserved.
 *
 */

#include <iostream>
#include "cfiler_native.h"
#include "cfiler_nativePriv.h"

void cfiler_native::HelloWorld(const char * s)
{
	 cfiler_nativePriv *theObj = new cfiler_nativePriv;
	 theObj->HelloWorldPriv(s);
	 delete theObj;
};

void cfiler_nativePriv::HelloWorldPriv(const char * s) 
{
	std::cout << s << std::endl;
};

