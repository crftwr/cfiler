#ifndef __CFILER_NATIVE_H__
#define __CFILER_NATIVE_H__


extern PyTypeObject ProcessInternalLockFile_Type;
#define ProcessInternalLockFile_Check(op) PyObject_TypeCheck(op, &ProcessInternalLockFile_Type)

struct ProcessInternalLockFile_Object
{
    PyObject_HEAD
    HANDLE handle;
};


extern PyTypeObject CheckDir_Type;
#define CheckDir_Check(op) PyObject_TypeCheck(op, &CheckDir_Type)

struct CheckDir_Object
{
    PyObject_HEAD
    class CheckDir * p;
};


#endif /* __CFILER_NATIVE_H__ */
