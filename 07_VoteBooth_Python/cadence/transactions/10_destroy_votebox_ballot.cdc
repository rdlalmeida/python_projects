/**
    This transaction deletes a Ballot identified by an electionId provided (Ballots are stored under the linkedElectionId value as key inside VoteBoxes) from a VoteBox resource from the transaction signer's account.

    @param electionId (UInt64) The election identifier to retrieve the Ballot to delete from the VoteBox.
**/

import BallotStandard from 0xf8d6e0586b0a20c7
import VoteBoxStandard from 0xf8d6e0586b0a20c7

transaction(electionId: UInt64) {
    let voteboxRef: auth(VoteBoxStandard.VoteBoxAdmin, Storage) &VoteBoxStandard.VoteBox
    let voteboxOwner: Address
    prepare(signer: auth(VoteBoxStandard.VoteBoxAdmin, Storage) &Account) {
        self.voteboxRef = signer.storage.borrow<auth(VoteBoxStandard.VoteBoxAdmin, Storage) &VoteBoxStandard.VoteBox>(from: VoteBoxStandard.voteBoxStoragePath) ??
        panic(
            "Unable to retrieve a valid &VoteBoxStandard.VoteBox at "
            .concat(VoteBoxStandard.voteBoxStoragePath.toString())
            .concat(" from account ")
            .concat(signer.address.toString())
        )

        self.voteboxOwner = signer.address
    }

    execute {
        // There's a function in place just for these cases
        let burnedBallotId: UInt64? = self.voteboxRef.deleteBallot(electionId: electionId)

        // NOTE: The next logs only matter in the local emulator. For live net tests I need to capture the BallotBurned event instead
        if (burnedBallotId == nil) {
            log(
                "WARNING: The VoteBox in account "
                .concat(self.voteboxOwner.toString())
                .concat(" does not have a Ballot under electionId ")
                .concat(electionId.toString())
            )
        }
        else {
            log(
                "Ballot "
                .concat(burnedBallotId!.toString())
                .concat(" attached to Election ")
                .concat(electionId.toString())
                .concat(" destroyed from the VoteBox in account ")
                .concat(self.voteboxOwner.toString())
            )
        }
    }
}