from algopy import ARC4Contract, subroutine, Global, Asset, UInt64, gtxn, itxn, Txn
from algopy.arc4 import abimethod


class AsaMarketplace(ARC4Contract):
    def __init__(self) -> None:
        self.assetId = UInt64(0)
        self.price = UInt64(0)

    @abimethod()
    def set_asset(self, asset: Asset) -> UInt64:
        # opt-in
        itxn.AssetTransfer(
            xfer_asset=asset,
            asset_receiver=Global.current_application_address,
            asset_amount=0,
            fee=0
        ).submit()

        self.assetId = asset.id

        return asset.id
    
    @abimethod
    def list_for_sale(self, xfer: gtxn.AssetTransferTransaction, price: UInt64) -> None:
        assert xfer.asset_receiver == Global.current_application_address, "receiver is not the application"
        assert xfer.asset_amount > 0, "must be greater than zero"
        assert price > 0, "Invalid price"

        self.price = price

    @abimethod
    def delist(self) -> UInt64:
        assert Txn.sender == Global.creator_address, "Not application creator"

        available = self.total_asset_owned_by_application()
        assert available > 0, "No asset to delist"

        itxn.AssetTransfer(
            xfer_asset=self.assetId,
            asset_receiver=Global.creator_address,
            asset_amount=available,
            fee=0
        ).submit()

        return available

    @abimethod
    def buy(self, mbrPay: gtxn.PaymentTransaction, qty: UInt64) -> UInt64:
        assert mbrPay.receiver == Global.creator_address, "Must transfer to application creator"

        available = self.total_asset_owned_by_application()
        assert available >= qty, "Insufficient available asset"

        total_mbr = qty * self.price
        assert mbrPay.amount == total_mbr, "Insufficient payment"

        itxn.AssetTransfer(
            xfer_asset=self.assetId,
            asset_receiver=Txn.sender,
            asset_amount=qty,
            fee=0
        ).submit()

        return qty

    @subroutine
    def total_asset_owned_by_application(self) -> UInt64:
        return Asset(self.assetId).balance(Global.current_application_address)
