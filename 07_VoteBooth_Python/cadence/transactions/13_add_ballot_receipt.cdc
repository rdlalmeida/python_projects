/**
    Use this transaction to add the ballotReceipt provided as argument, to a VoteBox under the account used to sign this transaction, under the electionId provided as well.
    
    @param electionId (UInt64): The election identifier to select the internal dictionary entry to where this ballotReceipt is to be saved.
    @param ballotReceipt (UInt64): The ballotReceipt to add to the VoteBox stored in this account provided.
**/

import VoteBoxStandard from 0xf8d6e0586b0a20c7

transaction(electionId: UInt64, ballotReceipt: UInt64) {
    let voteBoxRef: &VoteBoxStandard.VoteBox

    prepare(signer: auth(Storage) &Account) {
        // Grab the authorised reference to the VoteBox, if the account and resource exist
        self.voteBoxRef = signer.storage.borrow<&VoteBoxStandard.VoteBox>(from: VoteBoxStandard.voteBoxStoragePath) ??
        panic(
            "Unable to retrieve a valid &VoteBoxStandard.VoteBox at "
            .concat(VoteBoxStandard.voteBoxStoragePath.toString())
            .concat(" from account ")
            .concat(signer.address.toString())
        )
    }

    execute {
        // Use the reference obtained from the signer account to submit the ballotReceipt for registration
        self.voteBoxRef.addBallotReceipt(electionId: electionId, ballotReceipt: ballotReceipt)
    }
}