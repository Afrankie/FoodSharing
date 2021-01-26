from  bottle  import  route ,  run ,  template

@route( '/hello/<name>' ) 
def  index ( name ): 
    return  template ( '<b> Hello {{name}} </ b>!' ,  name = name )

if  __name__  ==  '__main__' : 
    run ( host = '0.0.0.0' ,  port = 8080 ) 
else : 
    application  =  default_app ()

