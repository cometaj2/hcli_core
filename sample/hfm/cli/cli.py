import json
import io

class CLI:
    commands = None
    inputstream = None
    
    def __init__(self, commands, inputstream):
        self.commands = commands
        self.inputstream = inputstream

    def execute(self):

        if self.inputstream != None:
            self.upload()
            return None

        elif self.inputstream == None:
            return self.download()

    def upload(self):
        None

    def download(self):
        None

#    public InputStream execute(String[] commands, InputStream is) throws Exception
#    {
#        if(is != null)
#        {
#            upload(is);
#            return null;
#        }
#        else
#        {
#            return download();
#        }
#    }

#    private void upload(InputStream is) throws FileNotFoundException
#    {
#        if (is != null)
#        {
#            File f = new File("/Users/jeff/Desktop/test.mov");
#            FileOutputStream fos = new FileOutputStream(f);
#"CLI.java" 70L, 1752C
#            {
#                int bufferSize = 1048576;
#                byte[] b = new byte[bufferSize];
#                while ((bufferSize = is.read(b)) != -1)
#                {
#                   fos.write(b, 0, bufferSize);
#                   fos.flush();
#                }
#
#                is.close();
#                fos.close();
#            }
#            catch (IOException e)
#            {
#                e.printStackTrace();
#            }
#            finally
#            {
#                IOUtils.closeQuietly(is);
#                IOUtils.closeQuietly(fos);
#            }
#        }
#
#        return;
#    }
#
#    public InputStream download() throws FileNotFoundException
#    {
#        File attachment = new File("/Users/jeff/Desktop/DontStarve.mov");
#        final FileInputStream fis = new FileInputStream(attachment);
#
#        return fis;
#    }    
