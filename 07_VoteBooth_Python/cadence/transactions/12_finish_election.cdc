/**
    This transaction finishes an Election by setting the provided dictionary as the final election results and by setting the isFinished flag to true.

    @param electionResults ({String: Int}) The dictionary of election results to set in this election, in the format {election_option: vote_count}
    @param electionId (UInt64) The election identifier for the election to finish.
**/

import ElectionStandard from 0xf8d6e0586b0a20c7
import VoteBooth from 0xf8d6e0586b0a20c7

transaction(electionId: UInt64, electionResults: {String: Int}) {
    let electionIndexRef: &{VoteBooth.ElectionIndexPublic}
    let electionRef: auth(ElectionStandard.ElectionAdmin) &ElectionStandard.Election
    let deployerAddress: Address

    prepare(signer: auth(ElectionStandard.ElectionAdmin, BorrowValue) &Account) {
        self.deployerAddress = VoteBooth.deployerAddress

        let deployerAccount: &Account = getAccount(self.deployerAddress)

        self.electionIndexRef = deployerAccount.capabilities.borrow<&{VoteBooth.ElectionIndexPublic}>(VoteBooth.electionIndexPublicPath) ??
        panic(
            "Unable to retrieve a valid &{VoteBooth.ElectionIndexPublic} at `VoteBooth.electionIndexPublicPath.toString()` from account `self.deployerAddress.toString()`"
        )

        let electionStoragePath: StoragePath = self.electionIndexRef.getElectionStoragePath(electionId: electionId) ??
        panic(
            "Unable to get a valid StoragePath for Election `electionId.toString()` from the ElectionIndexPublic from account `self.deployerAddress.toString()`"
        )

        self.electionRef = signer.storage.borrow<auth(ElectionStandard.ElectionAdmin) &ElectionStandard.Election>(from: electionStoragePath) ??
        panic(
            "Unable to retrieve a valid auth(ElectionStandard.ElectionAdmin) &ElectionStandard.Election at `electionStoragePath.toString()` from account `self.deployerAddress.toString()`"
        )
    }

    execute {
        let result: Bool = self.electionRef.finishElection(electionResults: electionResults)

        if (result) {
            log(
                "Election `electionId.toString()` is finished!"
            )
        }
        else {
            log(
                "Election `electionId.toString()` did not finished correctly!"
            )
        }
    }
}