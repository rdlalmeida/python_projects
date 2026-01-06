/**
    This transactions submits a Ballot in storage for the electionId provided to the Election resource in question. This action relinquishes the ownership of the Ballot resource to the owner of the Election.

    @param _electionId (UInt64) The id of the Election to vote. Ballots are internally stored inside VoteBoxes using the associated electionId as key.
**/
import BallotStandard from 0xf8d6e0586b0a20c7
import VoteBoxStandard from 0xf8d6e0586b0a20c7

transaction(_electionId: UInt64) {
    let voteBoxRef: auth(BallotStandard.BallotAdmin) &VoteBoxStandard.VoteBox

    prepare(signer: auth(BallotStandard.BallotAdmin, BorrowValue) &Account) {
        self.voteBoxRef = signer.storage.borrow<auth(BallotStandard.BallotAdmin) &VoteBoxStandard.VoteBox>(from: VoteBoxStandard.voteBoxStoragePath) ??
        panic(
            "Unable to retrieve a valid auth(BallotStandard.BallotAdmin) &VoteBoxStandard at `VoteBoxStandard.voteBoxPublicPath.toString()` from account `signer.address.toString()`"
        )
    }

    execute {
        let returnedElectionId: UInt64 = self.voteBoxRef.castBallot(electionId: _electionId)

        if (returnedElectionId != _electionId) {
            panic(
                "ERROR: The Ballot was cast for Election `_electionId.toString()` but the transaction returned Election `returnedElectionId.toString()`"
            )
        }
    }
}