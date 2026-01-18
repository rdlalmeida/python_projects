/**
    Use this transaction to remove the ballotReceipt provided as argument, from a VoteBox stored under the account used to sign this transaction, under the electionId provided as well.

    @param electionId (UInt64): The election identifier to select the internal dictionary entry to where the ballotReceipt is to be removed from.
    @param ballotReceipt (UInt64): The ballotReceipt to remove from the VoteBox stored in the account provided.
**/
import VoteBoxStandard from 0xf8d6e0586b0a20c7

transaction(electionId: UInt64, ballotReceipt: UInt64) {
    let voteBoxRef: &VoteBoxStandard.VoteBox
    let voterAddress: Address

    prepare(signer: auth(Storage) &Account) {
        // Grab the authorized reference to the VoteBox, if the account and resource exists
        self.voteBoxRef = signer.storage.borrow<&VoteBoxStandard.VoteBox>(from: VoteBoxStandard.voteBoxStoragePath) ??
        panic(
            "Unable to retrieve a valid &VoteBoxStandard.VoteBox at "
            .concat(VoteBoxStandard.voteBoxStoragePath.toString())
            .concat(" from account ")
            .concat(signer.address.toString())
        )

        self.voterAddress = signer.address
    }

    execute {
        // Use the reference obtained from the signer account to submit the removal of the ballotReceipt provided
        let ballotReceiptRemoved: UInt64? = self.voteBoxRef.removeBallotReceipt(electionId: electionId, ballotReceiptToRemove: ballotReceipt)
    }
}