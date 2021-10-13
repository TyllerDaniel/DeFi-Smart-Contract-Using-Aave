from scripts.helpful_scripts import get_account
from brownie import config,network,interface
from scripts.get_weth import get_weth
from web3 import Web3

amount = Web3.toWei(0.05,'ether')

def main():
    account = get_account()
    erc20_address = config["networks"][network.show_active()]["weth_token"]
    if network.show_active() in ["mainnet-fork"]:
        get_weth()
    lending_pool = get_lending_pool()
    approve_erc20(amount,lending_pool.address, erc20_address,account)
    print("Depositing Token....")
    tx = lending_pool.deposit(erc20_address, amount, account.address, 0,{"from":account})
    tx.wait(1)
    print("Deposited!!!......")
    borrowable_eth, total_debt= get_borrowable_data(lending_pool,account)
    print("Let's Borrow!!")
    #We Will need to get DAI in terms of Ethereum
    dai_eth_price = get_asset_price(config["networks"][network.show_active()]["dai_eth_price_feed"])
    amount_dai_to_borrow = (1 / dai_eth_price) * (borrowable_eth * 0.95)
    #Converting borrowable_eth to borrowable_dai * 95%
    print(f"We are going to borrow {amount_dai_to_borrow} DAI")
    #Borrowing.
    dai_address = config["networks"][network.show_active()]["dai_token"]
    borrow_tx = lending_pool.borrow(dai_address, Web3.toWei(amount_dai_to_borrow,"ether") , 1, 0, account.address,{"from":account})
    borrow_tx.wait(1)
    print("Borrowed Some DAI")
    get_borrowable_data(lending_pool,account)
    repay_all(amount,lending_pool,account)
    print("You just deposited,borrowed and repaid with Aave,Brownie and Chainlink ")

def repay_all(amount,lending_pool,account):
    approve_erc20(Web3.toWei(amount,"ether"),lending_pool,config["networks"][network.show_active()]["dai_token"],account)
    repay_tx = lending_pool.repay(config["networks"][network.show_active()]["dai_token"],amount,1,account.address, {"from":account})
    repay_tx.wait(1)
    print("Repaid")




def get_asset_price(price_feed_address):
    dai_eth_price_feed = interface.AggregatorV3Interface(price_feed_address)
    latest_price = dai_eth_price_feed.latestRoundData()[1]
    converted_latest_price = Web3.fromWei(latest_price,'ether')
    print(f"The DAI/ETH Price is {converted_latest_price}")
    return float(converted_latest_price)

def get_borrowable_data(lending_pool,account):
    (total_Collateral_ETH,
    total_Debt_ETH,
    available_Borrows_ETH,
    current_Liquidation_Threshold,
    ltv,
    health_Factor)= lending_pool.getUserAccountData(account.address)
    available_Borrows_ETH = Web3.fromWei(available_Borrows_ETH,"ether")
    total_Collateral_ETH = Web3.fromWei(total_Collateral_ETH,"ether")
    total_Debt_ETH = Web3.fromWei(total_Debt_ETH,"ether")
    print(f"You have {total_Collateral_ETH} worth of ETH deposited")
    print(f"You have {total_Debt_ETH} worth of ETH borrowed")
    print(f"You can borrow {available_Borrows_ETH} worth of ETH")
    return(float(available_Borrows_ETH),float(total_Debt_ETH))


    
def approve_erc20(amount,spender,erc20_address,account):
    print("Approving ERC20 token.....")
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(spender,amount,{"from":account})
    tx.wait(1)
    print("Approved!")
    return tx
    



def get_lending_pool():
    lending_pool_addresses_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_addresses_provider"]
    )
    lending_pool_address = lending_pool_addresses_provider.getLendingPool()
    lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool