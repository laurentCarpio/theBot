# %%
from trade_bot.utils.trade_logger import logger
from trade_bot.my_bitget import MyBitget
from trade_bot.extract_transform import ExtractTransform
import time


# Create a single global instance to connect
my_bitget = MyBitget()

def find_opportunities():
    while True:
        for the_symbol in my_bitget.get_all_symbol():
            # iterate through all the granularity (frequency)
            logger.debug('###########################################')
            logger.debug(f'{the_symbol} : checking....')
            my_etl = ExtractTransform(the_symbol, my_bitget)
            if my_etl.find_candidat():
                if my_etl.prep_row():
                    logger.info(f'{the_symbol} : validated')
                    clientOid = my_bitget.place_order(my_etl.get_row())
                    my_etl.display_chart(clientOid, display= False)
        logger.info("end of the for iteration, go to sleep before new iteration")
        time.sleep(3600)

if __name__ == '__main__':
     find_opportunities()

# the command to create an image of the app for docker 
# docker build -t trading-bot .
# the command to start the application locally on docker.desktop 
# docker run --rm trading-bot
# to export the image to the aws container 
# aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin 174175447862.dkr.ecr.us-east-2.amazonaws.com
# to tag the image before pushing it to the aws container 
# docker tag trading-bot:latest 174175447862.dkr.ecr.us-east-2.amazonaws.com/tradebot:latest
# to push it to the container 
# docker push 174175447862.dkr.ecr.us-east-2.amazonaws.com/tradebot:latest   
# the aws container is in east-2 : 
# https://us-east-2.console.aws.amazon.com/ecr/private-registry/repositories?region=us-east-2 


