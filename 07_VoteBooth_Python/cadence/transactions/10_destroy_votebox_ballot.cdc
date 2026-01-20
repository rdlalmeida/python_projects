/**
    This transaction deletes a Ballot identified by an electionId provided (Ballots are stored under the linkedElectionId value as key inside VoteBoxes) from a VoteBox resource from the transaction signer's account.

    @param electionId (UInt64) The election identifier to retrieve the Ballot to delete from the VoteBox.
**/

import BallotStandard from 0x287f5c8b0865c516
import VoteBoxStandard from 0x287f5c8b0865c516

transaction(electionId: UInt64) {
    let voteboxRef: auth(VoteBoxStandard.VoteBoxAdmin, LoadValue) &VoteBoxStandard.VoteBox
    let voteboxOwner: Address
    prepare(signer: auth(VoteBoxStandard.VoteBoxAdmin, Storage) &Account) {
        self.voteboxRef = signer.storage.borrow<auth(VoteBoxStandard.VoteBoxAdmin, LoadValue) &VoteBoxStandard.VoteBox>(from: VoteBoxStandard.voteBoxStoragePath) ??
        panic(
            "Unable to retrieve a valid &VoteBoxStandard.VoteBox at `VoteBoxStandard.voteBoxStoragePath.toString()` from account `signer.address.toString()`"
        )

        self.voteboxOwner = signer.address
    }

    execute {
        // There's a function in place just for these cases
        let burnedBallotId: UInt64? = self.voteboxRef.deleteBallot(electionId: electionId)
    }
}