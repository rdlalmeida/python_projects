/**
    Transaction to deliver a Ballot, currently inside a VoteBox in this transaction signer's account, to the VoteBox of another voter. This transaction receives an electionId and a recipient address. It uses the electionId to validate that a Ballot exists for the electionId provided in the transaction signer's VoteBox and validates that the recipient address provided contains a valid VoteBox, and that it does not have a Ballot for the electionId provided as well. If all is correct, the Ballot for the electionId provided is deposited to the recipient address account.

    @param electionId (UInt64): The electionId for the Ballot to delegate to the recipient address.
    @param recipientAddress (Address): The account address to where the Ballot is to be delivered to.
**/
import VoteBoxStandard from 0x9a0766d93b6608b7
import BallotStandard from 0x9a0766d93b6608b7

transaction(electionId: UInt64, recipientAddress: Address) {
    let signerVoteBoxRef: auth(VoteBoxStandard.VoteBoxAdmin) &VoteBoxStandard.VoteBox
    
    prepare(signer: auth(LoadValue, SaveValue, BorrowValue, VoteBoxStandard.VoteBoxAdmin) &Account) {
        // Grab an authorised reference to the signer's VoteBox
        self.signerVoteBoxRef = signer.storage.borrow<auth(VoteBoxStandard.VoteBoxAdmin) &VoteBoxStandard.VoteBox>(from: VoteBoxStandard.voteBoxStoragePath) ??
        panic(
            "Unable to retrieve a valid &VoteBoxStandard.VoteBox at "
            .concat(VoteBoxStandard.voteBoxStoragePath.toString())
            .concat(" from account ")
            .concat(signer.address.toString())
        )
    }

    execute {
        // And run the respective function. The contract function already validates everything else, so there's no point in doubling the validation step here.
        self.signerVoteBoxRef.delegateBallot(electionId: electionId, recipientAddress: recipientAddress)
    }
}