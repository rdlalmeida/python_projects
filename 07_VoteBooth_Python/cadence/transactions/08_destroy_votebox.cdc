/**
    This transaction loads and destroys a VoteBox resource from the transaction signer's storage account.
**/
import VoteBoxStandard from 0x287f5c8b0865c516
import Burner from 0x9a0766d93b6608b7

transaction() {
    let voteBoxToDestroy: @AnyResource?

    prepare(signer: auth(LoadValue, UnpublishCapability) &Account) {
        // Try to load the VoteBox resource
        self.voteBoxToDestroy <- signer.storage.load<@AnyResource>(from: VoteBoxStandard.voteBoxStoragePath) ??
        panic(
            "ERROR: Account `signer.address.toString()` does not have a VoteBox stored at `VoteBoxStandard.voteBoxStoragePath.toString()`"
        )
    }

    execute {
        // Done. Destroy it
        Burner.burn(<- self.voteBoxToDestroy)
    }
}